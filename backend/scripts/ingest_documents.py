""" 
DOcument Ingestion Pipeline - populates the chromaDB knowledge base .

Pipeline : Sample Documents -> RecusriveCharacterTextSplitter -> Huggingface Embeddings -> ChromDB

Uses Synthetic SEC filling data for 5 companies (NVDA , AAPL , TSLA , MSFT , JPM)
In production , You would use Langchain,s Documentloader 

"""