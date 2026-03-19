"""FastAPI backend for Video RAG application."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from config.settings import settings
from utils.youtube_utils import extract_video_id, get_transcript, transcript_to_text
from utils.text_processing import create_chunks_with_metadata
from rag.pipeline import RAGPipeline
from rag.embeddings import EmbeddingsManager

# Initialize FastAPI app
app = FastAPI(
    title="Video RAG API",
    description="API for YouTube video Q&A using RAG pipeline",
    version="1.0.0"
)

# Initialize services
embeddings_manager = EmbeddingsManager(api_key=settings.openai_api_key)
rag_pipeline = RAGPipeline(api_key=settings.openai_api_key)
print(f"backend key: {settings.openai_api_key}")
# Store session data (in production, use a proper database)
sessions: Dict[str, Any] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class YouTubeURLRequest(BaseModel):
    """Request model for YouTube URL."""
    url: str = Field(..., description="YouTube URL or video ID")
    languages: Optional[List[str]] = Field(
        default=["en"],
        description="Preferred transcript languages"
    )


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())


class ChatQueryRequest(BaseModel):
    """Request model for chat query."""
    session_id: str = Field(..., description="Session identifier")
    query: str = Field(..., description="User query")


class VerificationResult(BaseModel):
    """Answer verification result."""
    is_grounded: bool = Field(..., description="Is answer grounded in context?")
    has_hallucinations: bool = Field(..., description="Does answer contain hallucinations?")
    is_relevant: bool = Field(..., description="Is answer relevant to query?")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    explanation: str = Field(..., description="Explanation of verification")


class Source(BaseModel):
    """Source chunk."""
    text: str = Field(..., description="Chunk text")
    chunk_id: int = Field(..., description="Chunk ID")
    source: str = Field(..., description="Source identifier")


class ChatQueryResponse(BaseModel):
    """Response model for chat query."""
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source chunks")
    verification: Optional[VerificationResult] = Field(
        None,
        description="Answer verification results"
    )
    confidence: float = Field(default=0.0, description="Answer confidence score")


class ProcessingStatus(BaseModel):
    """Status of video processing."""
    status: str = Field(..., description="'processing', 'completed', 'error'")
    message: str = Field(..., description="Status message")
    video_id: Optional[str] = Field(None, description="Video ID")
    chunks_count: Optional[int] = Field(None, description="Number of chunks")


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str = Field(..., description="Session ID")
    video_id: str = Field(..., description="YouTube video ID")
    created_at: str = Field(..., description="Creation timestamp")
    messages_count: int = Field(..., description="Number of messages")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Video RAG API",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# YouTube Processing Endpoints
# ============================================================================

@app.post("/api/process_video", response_model=ProcessingStatus)
async def process_video(request: YouTubeURLRequest, background_tasks: BackgroundTasks):
    """
    Process YouTube video and build embeddings index.
    
    Args:
        request: YouTubeURLRequest with URL and language preferences
        background_tasks: FastAPI background tasks
        
    Returns:
        Processing status
    """
    import traceback
    try:
        # Extract video ID
        video_id = extract_video_id(request.url)
        if not video_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL or video ID"
            )
        
        try:
            # Get transcript
            transcript = get_transcript(video_id, languages=request.languages)
            if not transcript:
                raise HTTPException(
                    status_code=400,
                    detail="Could not retrieve transcript for this video"
                )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Convert transcript to text
        transcript_text = transcript_to_text(transcript)
        if not transcript_text:
            raise HTTPException(
                status_code=400,
                detail="Transcript is empty"
            )
        
        # Create chunks
        chunks = create_chunks_with_metadata(
            transcript_text,
            source=video_id,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Build embeddings index in background
        background_tasks.add_task(
            build_embeddings_async,
            chunks,
            video_id
        )
        
        return ProcessingStatus(
            status="processing",
            message=f"Video {video_id} is being processed",
            video_id=video_id,
            chunks_count=len(chunks)
        )
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] Exception in /api/process_video: {e}")
        print(tb)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )


import traceback

async def build_embeddings_async(chunks: List[Dict], video_id: str):
    """Build embeddings asynchronously."""
    try:
        # Clear previous index
        embeddings_manager.clear_index()
        
        # Build new index
        success = embeddings_manager.build_index(chunks)
        if success:
            # Store session data
            session_id = video_id
            sessions[session_id] = {
                "video_id": video_id,
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "chunks_count": len(chunks)
            }
            print(f"Successfully built index for video {video_id}")
        else:
            print(f"Failed to build index for video {video_id}")
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] Exception in build_embeddings_async: {e}")
        print(tb)


# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/api/chat", response_model=ChatQueryResponse)
async def chat(request: ChatQueryRequest):
    """
    Process user query and return answer with sources.
    
    Args:
        request: ChatQueryRequest with session_id and query
        
    Returns:
        ChatQueryResponse with answer, sources, and verification
    """
    try:
        # Check if embeddings index is loaded
        if not embeddings_manager.index:
            if not embeddings_manager.load_index():
                raise HTTPException(
                    status_code=400,
                    detail="No video processed yet. Please process a video first."
                )
        
        # Process query through RAG pipeline
        result = rag_pipeline.process_query(request.query)
        
        # Store message in session
        if request.session_id in sessions:
            sessions[request.session_id]["messages"].append({
                "role": "user",
                "content": request.query,
                "timestamp": datetime.now().isoformat()
            })
            sessions[request.session_id]["messages"].append({
                "role": "assistant",
                "content": result["answer"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only recent messages
            if len(sessions[request.session_id]["messages"]) > settings.max_history_messages:
                sessions[request.session_id]["messages"] = \
                    sessions[request.session_id]["messages"][-settings.max_history_messages:]
        
        # Format response
        verification_result = None
        if result.get("verification"):
            verification_result = VerificationResult(**result["verification"])
        
        sources = [Source(**source) for source in result.get("sources", [])]
        
        return ChatQueryResponse(
            answer=result["answer"],
            sources=sources,
            verification=verification_result,
            confidence=result.get("confidence", 0.0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/chat_history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of chat messages
    """
    try:
        if session_id not in sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        messages = sessions[session_id].get("messages", [])
        return [ChatMessage(**msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )


# ============================================================================
# Session Management
# ============================================================================

@app.get("/api/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    List all active sessions.
    
    Returns:
        List of SessionInfo objects
    """
    return [
        SessionInfo(
            session_id=sid,
            video_id=data.get("video_id", "unknown"),
            created_at=data.get("created_at", ""),
            messages_count=len(data.get("messages", []))
        )
        for sid, data in sessions.items()
    ]


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Deletion status
    """
    try:
        if session_id not in sessions:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}"
        )


@app.post("/api/clear_all")
async def clear_all():
    """
    Clear all sessions and embeddings index.
    
    Returns:
        Clearing status
    """
    try:
        sessions.clear()
        embeddings_manager.clear_index()
        return {"status": "cleared", "message": "All sessions and index cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data: {str(e)}"
        )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "title": "Video RAG API",
        "description": "Chat with YouTube videos using RAG",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "process_video": "POST /api/process_video",
            "chat": "POST /api/chat",
            "chat_history": "GET /api/chat_history/{session_id}",
            "sessions": "GET /api/sessions",
            "delete_session": "DELETE /api/sessions/{session_id}",
            "clear_all": "POST /api/clear_all"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )
