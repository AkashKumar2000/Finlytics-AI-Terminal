"""
AI Research Agent - two-step pipeline:
  1. Tool-calling agent  (llama3-groq-70b-8192-tool-use-preview) — fetches data
  2. Synthesis LLM call  (llama-3.3-70b-versatile) — formats results as JSON

Keeping these two steps separate prevents the model from confusing
"call a tool" with "generate JSON output", which caused malformed function calls.
"""

import json
import logging
import re
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor

from app.config import settings
from app.ai.tools.market_data import get_stock_data, get_historical_prices, compare_companies
from app.ai.tools.news_search import search_financial_news
from app.ai.tools.document_search import search_financial_documents

logger = logging.getLogger("ai_agent")

# All available tools
TOOLS = [
    get_stock_data,
    get_historical_prices,
    compare_companies,
    search_financial_news,
    search_financial_documents,
]

# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert investment research analyst AI assistant specialising in Indian equity markets
(NSE and BSE). You help financial analysts conduct thorough, structured research on Indian companies, stocks, and markets.

IMPORTANT RULES:
1. ALWAYS use the available tools to fetch real data. NEVER make up financial numbers.
2. Decide which tools to call based on what the user is asking:
   - Stock prices, metrics, fundamentals → use get_stock_data (use .NS suffix for NSE, .BO for BSE)
   - Historical price trends, charts → use get_historical_prices
   - Comparing multiple companies → use compare_companies
   - Recent news, sentiment → use search_financial_news
   - SEBI filings, Annual Reports, Quarterly Results, DRHP details → use search_financial_documents
3. Only call the tools that are relevant. If user asks about news only, don't fetch stock data.
4. For comprehensive analysis, use multiple tools in combination.
5. ALWAYS attribute your data to the source (which tool/API provided it).
6. Use Indian financial conventions:
   - Currency is ₹ (INR). Format large numbers as ₹X Lakh Crore or ₹X Crore (not billions/millions).
   - Regulatory body is SEBI (not SEC). Exchange is NSE/BSE (not NYSE/NASDAQ).
   - Filing types: Annual Report, Quarterly Results (Q1/Q2/Q3/Q4), DRHP, Corporate Announcements.
   - Financial year runs April–March (FY25 = April 2024 – March 2025).
   - Use Indian financial news sources: Economic Times, Moneycontrol, Livemint, Business Standard.

OUTPUT FORMAT:
You must respond with a valid JSON object (no markdown, no code fences) with this structure:
{{
    "title": "A clear title for this research report",
    "summary": "2-3 sentence executive summary of findings",
    "sections": [
        {{
            "type": "company_overview | financial_metrics | comparison_table | price_chart | news_sentiment | risk_assessment | document_insights",
            "title": "Section title",
            "content": "Detailed analysis text for this section",
            "data": {{}} // structured data relevant to this section type
        }}
    ],
    "companies_analyzed": ["RELIANCE.NS", "HDFCBANK.NS"],
    "sources": [
        {{"source": "Yahoo Finance", "type": "market_data", "detail": "Stock price and metrics (NSE)"}},
        {{"source": "NewsAPI", "type": "news", "detail": "Recent news articles"}},
        {{"source": "BSE Filing - Quarterly Results", "type": "document", "detail": "Q3 FY25 results"}}
    ],
    "generated_at": "ISO timestamp"
}}

Section type guidelines:
- "company_overview": company info card (name, sector, price in ₹, market cap in ₹ Crore)
- "financial_metrics": key metrics (P/E, EPS in ₹, margins, revenue growth) — include raw data in "data" field
- "comparison_table": side-by-side comparison — data field should have an array of objects
- "price_chart": historical prices — data field should have the price array for charting
- "news_sentiment": news articles with sentiment — data field should have articles array
- "risk_assessment": risks and concerns (regulatory/SEBI, sector-specific, macro India risks)
- "document_insights": information from Annual Reports, Quarterly Results, or DRHP filings

Be thorough, analytical, and professional. Present both opportunities and risks."""


def _create_tool_agent() -> AgentExecutor:
    """Create and return the LangChain research agent.

    Returns an AgentExecutor that:
    1. Takes a user query
    2. Uses ChatGroq to decide which tools to call
    3. Executes tools (market data, news, documents)
    4. Synthesizes results into structured JSON
    """
    llm = ChatGroq(
        model= settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature= settings.LLM_TEMPERATURE,
        max_tokens=4096,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm,
                                    tools=TOOLS,
                                    prompt=prompt,
                                    )

    executor= AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=8,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

    return executor




async def run_research_query(query: str) -> dict:

    """Execute a research query through the AI agent and return structured results.

    This is the main function called by the API endpoint.

    Args:
        query: Natural language research query from the user

    Returns:
        dict with structured research results, sources, and metadata
    """

    try:
        # Step 1: tool-calling agent fetches raw data
        executor = _create_tool_agent()
        # Run the agent (ainvoke for async)
        result = await executor.ainvoke({"input": query})

        
        # Extract the output
        output = result.get("output", "")

        # Parse the structured JSON from the agent's response
        parsed = _parse_agent_output(output)

        # Extract tool call metadata from intermediate steps
        tool_calls = []
        for step in result.get("intermediate_steps", []):
            action, observation = step
            tool_calls.append({
                "tool": action.tool,
                "input": str(action.tool_input),
            })

        parsed["tool_calls"] = tool_calls
        return parsed
    except Exception as e:
        logger.error(f"Research query failed: {e}", exc_info=True)
        return {
            "title": "Research Query Error",
            "summary": f"An error occurred while processing your query: {str(e)}",
            "sections": [],
            "companies_analyzed": [],
            "sources": [],
            "error": str(e),
        }


def _parse_agent_output(output: str) -> dict:
    """Parse the agent's output into structured JSON.

    The LLM sometimes wraps JSON in prose or code fences — we try four
    extraction strategies before falling back to a plain-text wrapper.
    """
    # Strategy 1: output is already valid JSON
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: JSON inside ```json … ``` fence (anywhere in the string)
    m = re.search(r"```json\s*([\s\S]*?)\s*```", output)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: JSON inside ``` … ``` fence (no language tag)
    m = re.search(r"```\s*([\s\S]*?)\s*```", output)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 4: extract the outermost { … } block
    start = output.find("{")
    end = output.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(output[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse agent output as JSON, wrapping as text")
    return {
        "title": "Research Analysis",
        "summary": output[:500] if len(output) > 500 else output,
        "sections": [
            {
                "type": "document_insights",
                "title": "Analysis",
                "content": output,
                "data": {},
            }
        ],
        "companies_analyzed": [],
        "sources": [],
    }
