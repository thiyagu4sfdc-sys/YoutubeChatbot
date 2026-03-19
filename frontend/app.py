"""Streamlit Frontend for Video RAG Application."""
import streamlit as st
import requests
import json
from typing import Optional, List, Dict
from datetime import datetime
import time

# ============================================================================
# Configuration
# ============================================================================

st.set_page_config(
    page_title="Video RAG Chat",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint (configurable)
API_BASE_URL = st.secrets.get("api_url", "http://localhost:8000")

# ============================================================================
# Session State Initialization
# ============================================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None

if "processing" not in st.session_state:
    st.session_state.processing = False

if "index_ready" not in st.session_state:
    st.session_state.index_ready = False


# ============================================================================
# Helper Functions
# ============================================================================

def check_api_health() -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def process_video(url: str, languages: List[str] = None) -> Dict:
    """
    Process YouTube video via API.
    
    Args:
        url: YouTube URL
        languages: Preferred languages
        
    Returns:
        Response from API
    """
    if not languages:
        languages = ["en"]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/process_video",
            json={"url": url, "languages": languages},
            timeout=30
        )
        return response.json()
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        return None


def send_query(query: str) -> Optional[Dict]:
    """
    Send chat query to API.
    
    Args:
        query: User query
        
    Returns:
        Response from API
    """
    if not st.session_state.session_id:
        st.error("No session ID. Please process a video first.")
        return None
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                "session_id": st.session_state.session_id,
                "query": query
            },
            timeout=60
        )
        return response.json()
    except Exception as e:
        st.error(f"Error sending query: {str(e)}")
        return None


def get_chat_history() -> List[Dict]:
    """Get chat history from API."""
    if not st.session_state.session_id:
        return []
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/chat_history/{st.session_state.session_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def format_confidence(confidence: float) -> str:
    """Format confidence score with visual indicator."""
    bar_length = int(confidence * 20)
    bar = "█" * bar_length + "░" * (20 - bar_length)
    return f"{bar} {confidence:.1%}"


def display_verification(verification: Dict):
    """Display verification results."""
    if not verification:
        return
    
    with st.expander("📊 Answer Verification Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Confidence",
                f"{verification.get('confidence', 0):.1%}"
            )
        
        with col2:
            grounded = "✓ Yes" if verification.get("is_grounded") else "✗ No"
            st.metric("Grounded in Context", grounded)
        
        col3, col4 = st.columns(2)
        
        with col3:
            hallucinations = "✗ None" if not verification.get("has_hallucinations") else "⚠ Detected"
            st.metric("Hallucinations", hallucinations)
        
        with col4:
            relevant = "✓ Yes" if verification.get("is_relevant") else "✗ No"
            st.metric("Relevant", relevant)
        
        st.write(f"**Explanation:** {verification.get('explanation', 'N/A')}")


def display_sources(sources: List[Dict]):
    """Display source chunks."""
    if not sources:
        st.info("No sources retrieved.")
        return
    
    st.subheader("📚 Source Chunks")
    for i, source in enumerate(sources, 1):
        with st.expander(f"Source {i} (Chunk #{source.get('chunk_id', 'N/A')})"):
            st.write(source.get("text", ""))


# ============================================================================
# Main UI
# ============================================================================

def main():
    """Main application interface."""
    
    # Header
    st.title("🎥 Video RAG Chat")
    st.markdown("""
    Ask questions about YouTube videos using advanced RAG with answer verification.
    
    **How it works:**
    1. Paste a YouTube URL
    2. Wait for the video to be processed
    3. Ask questions about the video content
    4. Get answers grounded in the transcript with verification
    """)
    
    # Check API health
    if not check_api_health():
        st.error(
            "❌ API is not running! Please start the FastAPI backend:\n"
            "`uvicorn backend.main:app --reload`"
        )
        return
    
    st.success("✅ API Connected")
    
    # ========================================================================
    # Sidebar - Video Processing
    # ========================================================================
    
    with st.sidebar:
        st.header("🎬 Video Processing")
        
        # Video URL input
        youtube_url = st.text_input(
            "YouTube URL or Video ID",
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a full YouTube URL or just the video ID"
        )
        
        # Language selection
        languages = st.multiselect(
            "Transcript Languages",
            ["en", "es", "fr", "de", "zh", "ja"],
            default=["en"],
            help="Preferred languages for transcript (in order of preference)"
        )
        
        # Process button
        if st.button("🚀 Process Video", use_container_width=True):
            if not youtube_url:
                st.error("Please enter a YouTube URL or video ID")
            else:
                st.session_state.processing = True
                with st.spinner("Processing video... This may take a minute..."):
                    result = process_video(youtube_url, languages=languages)
                
                if result:
                    st.session_state.processing = False
                    
                    if result.get("status") == "processing":
                        st.success(
                            f"✅ Video processed!\n\n"
                            f"Video ID: {result.get('video_id')}\n"
                            f"Chunks: {result.get('chunks_count')}"
                        )
                        st.session_state.session_id = result.get("video_id")
                        st.session_state.current_video_id = result.get("video_id")
                        st.session_state.index_ready = True
                        st.session_state.chat_history = []
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('message')}")
        
        # Status indicator
        if st.session_state.session_id:
            st.info(
                f"📌 Active Session: `{st.session_state.session_id}`\n\n"
                f"Status: {'🟢 Ready' if st.session_state.index_ready else '🔄 Processing'}"
            )
        
        # Clear session button
        if st.button("🗑️ Clear Session", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.chat_history = []
            st.session_state.current_video_id = None
            st.session_state.index_ready = False
            st.success("Session cleared!")
            st.rerun()
    
    # ========================================================================
    # Main Area - Chat Interface
    # ========================================================================
    
    if not st.session_state.session_id:
        st.warning(
            "👈 **Please process a video first** to get started.\n\n"
            "Use the sidebar to enter a YouTube URL."
        )
        return
    
    # Chat history display
    st.subheader("💬 Chat History")
    
    chat_container = st.container()
    
    with chat_container:
        # Get and display chat history
        history = get_chat_history()
        
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "user":
                with st.chat_message("user"):
                    st.write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
    
    # Query input
    st.subheader("❓ Ask a Question")
    
    col1, col2 = st.columns([1, 0.15])
    
    with col1:
        user_query = st.text_input(
            "Your question about the video:",
            placeholder="What is the main topic of the video?",
            key="query_input"
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    # Process query
    if send_button and user_query:
        with st.spinner("Thinking..."):
            response = send_query(user_query)
        
        if response:
            # Display answer
            st.subheader("📝 Answer")
            with st.chat_message("assistant"):
                st.write(response.get("answer", "No answer generated"))
            
            # Display confidence
            confidence = response.get("confidence", 0)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Answer Confidence", format_confidence(confidence))
            
            # Display verification
            verification = response.get("verification")
            if verification:
                display_verification(verification)
            
            # Display sources
            sources = response.get("sources", [])
            if sources:
                display_sources(sources)
                st.divider()
    
    # ========================================================================
    # Example Queries
    # ========================================================================
    
    with st.expander("💡 Example Questions"):
        st.write("""
        Try asking questions like:
        - "What is the main topic of this video?"
        - "What are the key points discussed?"
        - "Who is mentioned in the video?"
        - "What are the key takeaways?"
        - "Can you summarize the video?"
        - "What specific examples are given?"
        """)
    
    # ========================================================================
    # Footer
    # ========================================================================
    
    st.divider()
    st.markdown("""
    ---
    **Video RAG App** | Advanced RAG with Answer Verification
    
    Built with FastAPI, Streamlit, OpenAI, and FAISS
    """)


if __name__ == "__main__":
    main()
