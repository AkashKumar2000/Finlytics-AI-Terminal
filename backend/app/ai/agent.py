"""
AI Research Agent - Langchain tool-calling agent that orchestrates financial research .

Architecture :
    User Query -> Agent(Claude via ChatAnthropic)->decides which tool to call->
    executes tools(market data , news , documents)-> syntesizes strucutured response

Key Langchain concepts used:
 - ChatAnthropic : LLM wrapper for claude
 - @tool : decorated functions become agent tools
 - create_tool_calling_agent: creates an agent that uses claude's native tool calling 
 - AgentExecutor : runs the agent loop (think -> act-> observe -> think->...)
 - ChatPromptTemplate : strcutres the system prompt + user input + agent scratchpad


The agent is AGENTIC - it decides which tool to call based on the query 
" Tell me about NVIDIA news"-> only calls news tool
" COmpare NVIDIA vs AMD financials "-> calls compare_Companies + maybe documents
" FUll analysis of Tesla "-> Calls all three tools
"""

import json 
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent , AgentExecutor

from app.config import settings
from app.ai.tools.market_data import get_stock_data, get_historical_prices, compare_companies
from app.ai.tools.news_search import search_financial_news
from app.ai.tools.document_search import search_financial_documents

logger = logging.getLogger("ai_agent")

#---------------ALL available tools----------

TOOLS= [
    get_stock_data,
    get_historical_prices,
    compare_companies,
    search_financial_news,
    search_financial_documents,
]

# --------------System Prompt---------------

SYSTEM_PROMPT = """You are an expert investment research analyst AI assistant. You help financial analysts
conduct thorough, structured research on companies, stocks, and markets.

IMPORTANT RULES:
1. ALWAYS use the available tools to fetch real data. NEVER make up financial numbers.
2. Decide which tools to call based on what the user is asking:
   - Stock prices, metrics, fundamentals → use get_stock_data
   - Historical price trends, charts → use get_historical_prices
   - Comparing multiple companies → use compare_companies
   - Recent news, sentiment → use search_financial_news
   - SEC filings, earnings details, deep fundamentals → use search_financial_documents
3. Only call the tools that are relevant. If user asks about news only, don't fetch stock data.
4. For comprehensive analysis, use multiple tools in combination.
5. ALWAYS attribute your data to the source (which tool/API provided it).

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
    "companies_analyzed": ["NVDA", "AMD"],
    "sources": [
        {{"source": "Yahoo Finance", "type": "market_data", "detail": "Stock price and metrics"}},
        {{"source": "NewsAPI", "type": "news", "detail": "Recent news articles"}},
        {{"source": "SEC Filing - 10-Q", "type": "document", "detail": "Q3 2024 quarterly report"}}
    ],
    "generated_at": "ISO timestamp"
}}

Section type guidelines:
- "company_overview": company info card (name, sector, price, market cap)
- "financial_metrics": key metrics (P/E, EPS, margins, growth) — include the raw data in "data" field
- "comparison_table": side-by-side comparison — data field should have an array of objects
- "price_chart": historical prices — data field should have the price array for charting
- "news_sentiment": news articles with sentiment — data field should have articles array
- "risk_assessment": risks and concerns
- "document_insights": information from SEC filings or earnings calls

Be thorough, analytical, and professional. Present both opportunities and risks."""

def create_research_agent()-> AgentExecutor:

    """ 
    Create and return the Langchain research agent . 

    Returns an AgentExecutor that :
    1.Takes a user query
    2. USes claude to decide which tools to call
    3. Executes tools(market data , news , documents)
    4. Synthesizes results into structured JSON
    """

    # INitialize claude LLM via Langchain
    llm = ChatGroq(
        model = settings.LLM_MODEL,
        api_key= settings.GROQ_API_KEY,
        temperature = settings.LLM_TEMPERATURE,
        max_tokens= 4096,

    )

    # Prompt template with agent scratchpad for tool calling loop
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # create agent - uses Claude's native tool calling (not React text parsing)

    agent= create_tool_calling_agent(
        llm= llm , 
        tools= TOOLS,
        prompt= prompt,
    )

    executor= AgentExecutor(
        agent= agent , 
        tools = TOOLS,
        verbose = True,             # Logs each step — great for debugging
        max_iterations = 10,        # Safety limit to prevent infinite loops
        return_intermediate_steps= True ,       # We can show which tools were called
        handle_parsing_errors= True  ,
    )

    return executor


async def run_research_query(query: str)->dict:

    """Execute a research query through the AI agent and return structured results .

    This is the main function called by the API endpoint .

    Args :
        query: NAtural language research query from the user 

    Returns:
        dict with structured results, sources and metadata
    """

    try: 

        executor = create_research_agent()

        # Run the agent ( ainvoke for async)
        result = await executor.ainvoke({"input": query})

        # Extract the output
        
        output = result.get("output", "")

        #Parse the structured JSON from the agent's response

        parsed = _parse_agent_output(output)

        #Extract tool call metadata from intermediate steps 
        tool_calls = []
        for step in result.get("intermediate_steps", []):
            action , observation = step
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


def _parse_agent_output(output : str)-> dict:
    """Parse the agent's output into structured JSON.

    The agent is prompted to return JSON, but LLMs can be unpredictable.
    This function handles edge cases gracefully.
    """

    # Try direct JSON parse
    try:
        # Strip markdown code fences if present
        cleaned = output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass


    # Fallback: wrap raw text in our expected structure
    logger.warning("Could not parse agent output as JSON, wrapping as text")

    return {
        "title": "Research Analysis",
        "summary": output[:500] if len(output) > 500 else output,
        "sections": [
            {
                "type": "company_overview",
                "title": "Analysis",
                "content": output,
                "data": {},
            }
        ],
        "companies_analyzed": [],
        
    }