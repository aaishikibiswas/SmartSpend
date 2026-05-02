import faiss
import numpy as np

# Simple FAISS wrapper for semantic search RAG (Retrieval-Augmented Generation)
class FAISSRetriever:
    def __init__(self, dimension: int = 256):
        # Create an L2 distance-based FAISS index
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []
        
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Seed the vector store with dummy FAQs or policy documents for SmartSpend."""
        faqs = [
            "SmartSpend tracks expenses based on the categories defined in standard banking formats.",
            "Alerts are sent when your daily budget falls below zero.",
            "You cannot change the budget manually; the app sets auto-budgets via behavior tracking.",
            "The ML system (XGBoost/LSTM) uses a rolling 7-day average to predict your next expense.",
            "If your spending risk is high, cut back on optional subscriptions and non-critical categories first."
        ]
        if not faqs:
            return
            
        # Normally we would use OpenAI embeddings API or similar. 
        # For local demonstration logic without network overhead during startup:
        # We simply use a dummy random embedding projection for these base rules.
        np.random.seed(42)
        embeddings = np.random.rand(len(faqs), self.dimension).astype('float32')
        self._add_texts(faqs, embeddings)

    def _add_texts(self, texts: list[str], embeddings_matrix: np.ndarray):
        self.documents.extend(texts)
        self.index.add(embeddings_matrix)

    def retrieve(self, query: str, top_k: int = 2) -> list[str]:
        if self.index.ntotal == 0:
            return []
        
        # Determine dummy query vector via same logic 
        # In a real system, you'd call client.embeddings.create(input=query)
        np.random.seed(abs(hash(query)) % (2**32))
        query_vec = np.random.rand(1, self.dimension).astype('float32')
        
        distances, indices = self.index.search(query_vec, top_k)
        
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.documents):
                results.append(self.documents[idx])
        return results

# Singleton instance
retriever = FAISSRetriever()
