"""
Document Ingestion Pipeline — loads real PDF filings into ChromaDB.

Pipeline: PDF files → PyPDFLoader → RecursiveCharacterTextSplitter →
          HuggingFaceEmbeddings → ChromaDB (collection: financial_documents)

Setup:
  1. Drop PDF files into backend/data/filings/
  2. Update backend/data/metadata.json with correct company/symbol/doc_type mappings
  3. Run: python -m scripts.ingest_documents  (from the backend/ directory)
"""
import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_chroma import Chroma
from app.config import settings

logging.basicConfig(level=logging.INFO , format="%(message)s")
logger = logging.getLogger(__name__)

METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metadata.json")
FILINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "filings")


def load_metadata()-> list[dict]:
    """
    Read metadata.json and return the list of file entries.
    """
    metadata_path = os.path.abspath(METADATA_PATH)
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"metadata.json not found at {metadata_path}. "
            "Create it following the template in backend/data/metadata.json."
        )

    with open(metadata_path, "r" , encoding="utf-8") as f:
        data = json.load(f)   # return python objec(dict , list ,....)  # json.load reads the json file
    return data.get("files" , [])

def ingest_documents():
    """
    RUn the FULL ingestion Pipeline
    """

    print("Starting the document ingetstion pipeline....")

    #--------Load metadata---
    print(f" loading metadata from data/metadata.json")
    file_entries = load_metadata()
    print(f" found {len(file_entries)} pdf files to process")

    # ---Text Spliterr
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size= 1000, 
        chunk_overlap= 200 , 
        length_function=len,
    )

    all_chunks=[]
    processed_companies =[]
    failed_files =[]

    for entry in file_entries:
        filename = entry["filename"]
        company = entry["company"]
        symbol = entry["symbol"]
        doc_type = entry.get("doc_type", "Document")
        filing_date = entry.get("filing_date", "")
        exchange = entry.get("exchange", "NSE")

        pdf_path = os.path.abspath(os.path.join(FILINGS_DIR, filename))

        print(f" Processing : {filename} ({company})")

        if not os.path.exists(pdf_path):
            print(f"file not found -skipping:{pdf_path}")
            failed_files.append(filename)
            continue
            
        try:
            loader= PyPDFLoader(pdf_path)
            pages = loader.load()
            print(f" Loaded pages : {len(pages)}")

            for page in pages:
                page.metadata.update({
                    "source": filename,
                    "company": company,
                    "symbol": symbol,
                    "doc_type": doc_type,
                    "filing_date": filing_date,
                    "exchange": exchange,
                    "section": doc_type,
                })

            chunks = text_splitter.split_documents(pages)
            print(f" Chunks created : { len(chunks)}\n")

            all_chunks.extend(chunks)
            if symbol not in processed_companies:
                processed_companies.append(symbol)
            
        except Exception as e:
            print(f"  Error processing {filename}: {e}\n")
            failed_files.append(filename)
            continue

    if not all_chunks:
        print(" No chunks to store — check that PDF files exist in data/filings/ and metadata.json is correct.")
        return

    print(f" Total chunks: {len(all_chunks)}")
    print(f" Companies: {', '.join(processed_companies)}")

    print("\n Loading embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    print(" Storing in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        collection_name="financial_documents",  # MUST match document_search.py
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )

    print(f"\n Ingestion complete!")
    print(f"   Documents processed: {len(file_entries) - len(failed_files)}")
    print(f"   Total chunks stored: {len(all_chunks)}")
    print(f"   Companies: {', '.join(processed_companies)}")
    print(f"   Vector store: {settings.CHROMA_PERSIST_DIR}")

    if failed_files:
        print(f"\n Skipped files ({len(failed_files)}): {', '.join(failed_files)}")

    # ── Verification query ─────────────────────────────────────
    if processed_companies:
        first_company = file_entries[0]["company"]
        verify_query = f"{first_company} revenue"
        print(f"\n🔍 Verification: \"{verify_query}\"")
        results = vector_store.similarity_search(verify_query, k=2)
        if results:
            for i, doc in enumerate(results):
                company_tag = doc.metadata.get("company", "Unknown")
                print(f"   Result {i + 1}: [{company_tag}] {doc.page_content[:120].strip()}...")
        else:
            print("   No results returned — check that embeddings were stored correctly.")


if __name__ == "__main__":
    ingest_documents()
    