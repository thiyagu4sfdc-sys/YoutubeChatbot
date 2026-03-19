"""RAG Pipeline with answer verification."""
from typing import List, Dict, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re
from config.settings import settings
from rag.embeddings import EmbeddingsManager


class RAGPipeline:
    """Retrieve-Augmented Generation pipeline with verification."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG pipeline.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or settings.openai_api_key
        self.embeddings_manager = EmbeddingsManager(api_key=self.api_key)
        
        # Initialize LLMs
        self.answer_llm = ChatOpenAI(
            model_name=settings.openai_model,
            api_key=self.api_key,
            temperature=0.3
        )
        
        self.verification_llm = ChatOpenAI(
            model_name=settings.openai_model_verification,
            api_key=self.api_key,
            temperature=0.2
        )
    
    def retrieve(self, query: str, k: int = None) -> List[Tuple[Dict, float]]:
        """
        Retrieve relevant chunks from vector store.
        
        Args:
            query: User query
            k: Number of chunks to retrieve
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if k is None:
            k = settings.max_retrieved_chunks
        
        try:
            results = self.embeddings_manager.search(query, k=k)
            return results
        except Exception as e:
            print(f"Error during retrieval: {str(e)}")
            return []
    
    def rerank_chunks(
        self,
        query: str,
        chunks: List[Tuple[Dict, float]]
    ) -> List[Tuple[Dict, float]]:
        """
        Re-rank retrieved chunks based on relevance to query.
        
        This is optional but improves answer quality by ensuring
        the most relevant chunks are prioritized.
        
        Args:
            query: User query
            chunks: List of (chunk_dict, similarity) tuples
            
        Returns:
            Re-ranked list of chunks
        """
        if not chunks:
            return []
        
        try:
            # Simple re-ranking based on query term overlap
            query_terms = set(query.lower().split())
            
            scored_chunks = []
            for chunk, similarity in chunks:
                chunk_text = chunk['text'].lower()
                chunk_terms = set(chunk_text.split())
                
                # Calculate term overlap score
                overlap = len(query_terms & chunk_terms)
                overlap_score = overlap / max(len(query_terms), 1)
                
                # Combine with original similarity score
                combined_score = (similarity * 0.5) + (overlap_score * 0.5)
                scored_chunks.append((chunk, combined_score))
            
            # Sort by combined score
            scored_chunks = sorted(scored_chunks, key=lambda x: x[1], reverse=True)
            return scored_chunks
        except Exception as e:
            print(f"Error during re-ranking: {str(e)}")
            return chunks
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> str:
        """
        Generate answer using retrieved context.
        
        Args:
            query: User query
            context_chunks: List of relevant chunks
            
        Returns:
            Generated answer
        """
        if not context_chunks:
            return "No relevant information found to answer your question."
        
        try:
            # Prepare context
            context_text = "\n\n".join([
                f"[Chunk {i+1}]\n{chunk['text']}"
                for i, chunk in enumerate(context_chunks)
            ])
            
            # Create prompt
            system_prompt = """You are a helpful assistant answering questions based on video transcripts.
Your task is to provide accurate, concise answers based ONLY on the provided context.
If the information is not in the context, say so clearly."""
            
            user_prompt = f"""Question: {query}

Context from video transcript:
{context_text}

Please provide a clear, accurate answer based on the context above."""
            
            # Generate answer
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.answer_llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def verify_answer(
        self,
        query: str,
        answer: str,
        context: str
    ) -> Dict[str, any]:
        """
        Verify answer correctness against context.
        
        This step checks if the answer is grounded in the provided context
        and not hallucinated.
        
        Args:
            query: Original query
            answer: Generated answer
            context: Retrieved context
            
        Returns:
            Dictionary with verification results
        """
        try:
            verification_prompt = f"""You are a verification expert. Your task is to verify if the given answer is accurate and grounded in the provided context.

Query: {query}

Answer: {answer}

Context from video:
{context}

Evaluate the answer based on:
1. Is the answer directly supported by the context? (Yes/No)
2. Are there any factual errors or hallucinations? (Yes/No)
3. Is the answer relevant to the query? (Yes/No)
4. Confidence score (0.0-1.0) of answer correctness

Respond in JSON format:
{{
    "is_grounded": true/false,
    "has_hallucinations": true/false,
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}}"""
            
            verification_messages = [
                SystemMessage(content="You are a verification expert. Respond only with valid JSON."),
                HumanMessage(content=verification_prompt)
            ]
            
            response = self.verification_llm.invoke(verification_messages)
            
            # Parse response
            try:
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    verification_result = json.loads(json_match.group())
                else:
                    verification_result = {
                        "is_grounded": True,
                        "has_hallucinations": False,
                        "is_relevant": True,
                        "confidence": 0.7,
                        "explanation": "Could not parse verification response"
                    }
            except json.JSONDecodeError:
                verification_result = {
                    "is_grounded": True,
                    "has_hallucinations": False,
                    "is_relevant": True,
                    "confidence": 0.7,
                    "explanation": "JSON parsing error"
                }
            
            return verification_result
        except Exception as e:
            return {
                "is_grounded": False,
                "has_hallucinations": False,
                "is_relevant": False,
                "confidence": 0.0,
                "explanation": f"Verification error: {str(e)}"
            }
    
    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process query through complete RAG pipeline.
        
        Args:
            query: User query
            
        Returns:
            Dictionary with answer, sources, and verification results
        """
        try:
            # Step 1: Retrieve relevant chunks
            retrieved_chunks = self.retrieve(query)
            if not retrieved_chunks:
                return {
                    "answer": "I couldn't find relevant information in the video to answer your question.",
                    "sources": [],
                    "verification": None,
                    "confidence": 0.0
                }
            
            # Step 2: Re-rank chunks
            reranked_chunks = self.rerank_chunks(query, retrieved_chunks)
            context_chunks = [chunk for chunk, _ in reranked_chunks[:settings.max_retrieved_chunks]]
            
            # Step 3: Generate answer
            answer = self.generate_answer(query, context_chunks)
            
            # Step 4: Prepare context for verification
            context_text = "\n\n".join([chunk['text'] for chunk in context_chunks])
            
            # Step 5: Verify answer
            verification = self.verify_answer(query, answer, context_text)
            
            # Step 6: Determine final confidence and apply threshold
            confidence = verification.get('confidence', 0.5)
            
            if not verification.get('is_grounded', False) or verification.get('has_hallucinations', False):
                if confidence < settings.confidence_threshold:
                    answer = f"I'm not confident in my answer. Based on the video, I cannot provide a reliable response to your question. Confidence: {confidence:.2f}"
                    confidence = 0.0
            
            # Prepare sources with chunk text and metadata
            sources = [
                {
                    "text": chunk['text'][:300] + "..." if len(chunk['text']) > 300 else chunk['text'],
                    "chunk_id": chunk.get('chunk_id', 0),
                    "source": chunk.get('source', 'transcript')
                }
                for chunk in context_chunks
            ]
            
            return {
                "answer": answer,
                "sources": sources,
                "verification": verification,
                "confidence": confidence
            }
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "verification": None,
                "confidence": 0.0
            }
