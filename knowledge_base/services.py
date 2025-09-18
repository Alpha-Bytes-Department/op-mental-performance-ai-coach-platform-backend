import os  
from .models import KnowledgeDocument
from .rag_pipeline import RAGPipeline

rag = RAGPipeline()

def load_documents():
    # Load all documents from DB into FAISS index.
    docs = []
    for doc in KnowledgeDocument.objects.all():
        with doc.document_file.open("rb") as f:
            text = f.read().decode("utf-8")
        docs.append({
            "id": str(doc.id), 
            "title": doc.title,
            "text": text,
            "domain": doc.domain,
        })
    if docs:
        rag.add_documents(docs)

def query_knowledge(query: str,domain:str = None):
    return rag.query(query,top_k=3,domain=domain)
