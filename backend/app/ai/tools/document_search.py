""""
Document knowledge Base Tool- Vector search over SEC fillings and earning reports.

This is Tool #3 of 3. Uses ChromaDB with HuggingFace embeddings.
The agent calls this when user asks about:
- SEC filings, earnings reports, fundamentals not in market data API
- Company-specific documents or analyst reports
- Deep-dive questions requiring document context

LangChain pipeline:
  DocumentLoader → RecursiveCharacterTextSplitter → HuggingFaceEmbeddings → ChromaDB


"""

import json 
import os 
from langchain_core.tools import tool

_vector_store = None

def get_vector_store():
    """
    Lazy-load the ChromaDB vector store. Creates it if it doesn't exist.
    """

    global _vector_store 

    if _vector_store is not None:
        return _vector_store

    from langchain_chroma import Chroma
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings
    from app.config import settings

    embeddings = HuggingFaceBgeEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs = {'device': 'cpu'},
    )

    _vector_store = Chroma(
        collection_name="financial_documents",
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )

    return _vector_store

@tool
def search_financial_documents(query: str)-> str:
    """Search the internal document knowledge base for SEC filings, earnings reports, and analyst notes.

    Use this tool when the user asks about:
    - SEC filings 
    - Earnings call transcripts or details
    - Company fundamentals not available via the stock data API
    - Specific financial metrics from reports (revenue breakdown, segment data)
    - Any question requiring document-level context

    Args:
        query: Natural language search query (e.g., "TCS data center revenue breakdown Q1 2026")

    Returns:
        JSON with relevant document chunks, their sources, and relevance scores.
    """

    try:
        store = get_vector_store()

        #Check if store has any documents
        collection = store._collection
        if collection.count() ==0:
            return json.dumps({
                "query": query,
                "results":[],
                "message": "Knowledge base is empty . Run the ingestion script to populate it",
                "source": "CHROMA DB(local)",
            })

        # USING MMR (maxicmal marginal relevance)- Give Diverge result for each chunk 
        
        docs = store.max_marginal_relevance_search(
            query= query, 
            k=5,      # return top 5 chunks
            fetch_k=20, # considering top 20 before MMR filtering
            lambda_mult = 0.7   # 0.7 = more relevance, 0.3 = more diversity
        )

        results= []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": {
                    "source": doc.metadata.get("source", "Unknown"),
                    "company": doc.metadata.get("company", "Unknown"),
                    "doc_type": doc.metadata.get("doc_type", "Unknown"),
                    "filing_date": doc.metadata.get("filing_date", "Unknown"),
                    "section": doc.metadata.get("section", "Unknown"),
                },
            })
        
        return json.dumps({
            "query": query,
            "results_count": len(results),
            "results" : results.append,
            "source" : "CHROMA DB(local knowledge base)"
            })

    except Exception as e:
        return json.dumps({
            "error": f"Document search failed: {str(e)}",
            "query": query,
            "source": "ChromaDB",
        })

