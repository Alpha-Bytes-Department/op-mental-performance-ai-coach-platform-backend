import os 
import faiss 
import numpy as np          
from typing import List,Dict 
from sentence_transformers import SentenceTransformer

class RAGPipeline:
    def __init__(self,model_name:str = "all-MiniLM-L6-v2") -> None:
        # Initialize embedding model and FAISS index 
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents: List[Dict] = []
        self.embeddings = None 

    def _embed_texts(self,texts:List[str]) -> np.ndarray:
        # Generate normalized embeddings for texts.
        embeddings = self.encoder.encode(texts,convert_to_numpy=True)
        embeddings = embeddings / np.linalg.norm(embeddings,axis=1,keepdims=True)
        return embeddings.astype("float32")
    
    def add_documents(self,docs: List[Dict]):
        new_embeddings = self._embed_texts([doc["text"] for doc in docs])
        if self.embeddings is None: 
            self.embeddings = new_embeddings
        else: 
            self.embeddings = np.vstack([self.embeddings,new_embeddings])

        self.index.add(new_embeddings)
        self.documents.extend(docs)

    def query(self, text:str,top_k: int = 3, domain:str= None) -> List[Dict]:
        # Search for relevant documents,optionallly filtered by domain
        if not self.documents:
            return []
        
        qurey_vec = self._embed_texts([text])
        scores,indices = self.index.search(qurey_vec,top_k)

        results = []
        for score,idx in zip(scores[0],indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                if domain and doc["domain"] != domain:
                    continue
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "text": doc["text"],
                    "domain": doc["domain"],
                    "similarity": float(score)
                })
        return results
        
