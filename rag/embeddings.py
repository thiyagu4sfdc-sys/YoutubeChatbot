"""Embeddings management and FAISS vector store utilities."""
import pickle
import os
import numpy as np
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import faiss
from langchain_openai import OpenAIEmbeddings
from config.settings import settings


class EmbeddingsManager:
    """Manage embeddings and FAISS vector store."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embeddings manager.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.openai_api_key
        print(f"RAG key: {settings.openai_api_key}")
        self.embeddings_model = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=self.api_key
        )
        self.index = None
        self.metadata = []  # Store chunk text and metadata
        self.index_path = settings.faiss_index_path
        self.metadata_path = settings.faiss_metadata_path
        
        # Ensure data directory exists
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        embeddings = self.embeddings_model.embed_documents(texts)
        return np.array(embeddings).astype('float32')
    
    def build_index(self, chunks: List[Dict]) -> bool:
        """
        Build FAISS index from chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'text' key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not chunks:
                raise ValueError("No chunks provided to build index")
            
            # Extract texts
            texts = [chunk['text'] for chunk in chunks]
            
            # Create embeddings
            embeddings = self.create_embeddings(texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            # Store metadata
            self.metadata = chunks
            
            # Save index and metadata
            self.save_index()
            
            return True
        except Exception as e:
            print(f"Error building FAISS index: {str(e)}")
            return False
    
    def save_index(self) -> bool:
        """
        Save FAISS index and metadata to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.index is None:
                raise ValueError("No index to save")
            
            # Save FAISS index
            os.makedirs(Path(self.index_path).parent, exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            print(f"Index saved to {self.index_path}")
            return True
        except Exception as e:
            print(f"Error saving FAISS index: {str(e)}")
            return False
    
    def load_index(self) -> bool:
        """
        Load FAISS index and metadata from disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.index_path):
                print(f"Index not found at {self.index_path}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            print(f"Index loaded from {self.index_path}")
            return True
        except Exception as e:
            print(f"Error loading FAISS index: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for similar chunks.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of (chunk_dict, distance) tuples sorted by similarity
        """
        if self.index is None or not self.metadata:
            # Try loading index from disk
            if not self.load_index():
                raise ValueError("Index not loaded and could not load from disk")

        try:
            # Create query embedding
            query_embedding = self.create_embeddings([query])[0]
            query_embedding = np.array([query_embedding]).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_embedding, k)
            
            # Retrieve results
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if 0 <= idx < len(self.metadata):
                    chunk = self.metadata[idx]
                    # Convert L2 distance to similarity score (0-1)
                    similarity = 1 / (1 + distance)
                    results.append((chunk, similarity))
            
            return results
        except Exception as e:
            print(f"Error searching index: {str(e)}")
            return []
    
    def index_exists(self) -> bool:
        """Check if index exists on disk."""
        return os.path.exists(self.index_path) and os.path.exists(self.metadata_path)
    
    def clear_index(self) -> bool:
        """
        Clear index from memory and disk.
        
        Returns:
            True if successful
        """
        try:
            self.index = None
            self.metadata = []
            
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            if os.path.exists(self.metadata_path):
                os.remove(self.metadata_path)
            
            return True
        except Exception as e:
            print(f"Error clearing index: {str(e)}")
            return False
