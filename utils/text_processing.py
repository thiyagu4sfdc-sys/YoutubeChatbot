"""Text processing and chunking utilities."""
import re
from typing import List, Dict, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter.
    
    This preserves semantic boundaries (paragraphs, sentences) better than
    simple character-based splitting.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        chunk_overlap: Characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    return chunks


def create_chunks_with_metadata(
    text: str,
    source: str = "transcript",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, any]]:
    """
    Create chunks with metadata (position, source, etc.).
    
    Args:
        text: Input text
        source: Source identifier (e.g., 'transcript', 'document')
        chunk_size: Characters per chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    text_chunks = splitter.split_text(text)
    
    chunks_with_metadata = []
    for idx, chunk in enumerate(text_chunks):
        position_in_text = text.find(chunk)
        
        chunks_with_metadata.append({
            "text": chunk,
            "source": source,
            "chunk_id": idx,
            "position": position_in_text,
            "length": len(chunk)
        })
    
    return chunks_with_metadata


def preprocess_text(text: str) -> str:
    """
    Preprocess text for better embedding quality.
    
    Args:
        text: Raw text
        
    Returns:
        Preprocessed text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\?!,;:\-]', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences while preserving punctuation.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Split on period, exclamation, question mark but keep them
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity using word overlap.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def get_text_summary(text: str, num_sentences: int = 3) -> str:
    """
    Get a simple summary by extracting first N sentences.
    
    Args:
        text: Input text
        num_sentences: Number of sentences to extract
        
    Returns:
        Summary text
    """
    sentences = split_into_sentences(text)
    summary_sentences = sentences[:num_sentences]
    return ' '.join(summary_sentences)
