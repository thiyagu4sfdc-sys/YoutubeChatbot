# API Testing Guide

## 📚 Complete API Testing and Examples

This guide provides curl commands and Python examples for testing all API endpoints.

## Prerequisites

```bash
# Backend running:
python -m uvicorn backend.main:app --reload

# In another terminal, you can test with:
curl http://localhost:8000/health
```

---

## 1. Health Check

**Test if API is running**

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Video RAG API",
  "timestamp": "2024-03-18T10:30:00.000000"
}
```

---

## 2. Process Video

**Extract transcript and build embeddings index**

### Example 1: Basic Video Processing

```bash
curl -X POST http://localhost:8000/api/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "languages": ["en"]
  }'
```

### Example 2: Multiple Languages

```bash
curl -X POST http://localhost:8000/api/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "languages": ["en", "es", "fr"]
  }'
```

### Example 3: Just Video ID

```bash
curl -X POST http://localhost:8000/api/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "jNQXAC9IVRw",
    "languages": ["en"]
  }'
```

**Response:**
```json
{
  "status": "processing",
  "message": "Video jNQXAC9IVRw is being processed",
  "video_id": "jNQXAC9IVRw",
  "chunks_count": 42
}
```

**Notes:**
- Processing happens in background
- Takes 30-90 seconds depending on video length
- Response returns immediately but processing continues

---

## 3. Chat Query (Main Endpoint)

**Ask a question about the processed video**

### Basic Query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "jNQXAC9IVRw",
    "query": "What is the main topic of this video?"
  }'
```

### Complex Query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "jNQXAC9IVRw",
    "query": "Can you explain the key takeaways and provide specific examples?"
  }'
```

**Response:**
```json
{
  "answer": "The main topic of the video is about YouTube's first video...",
  "sources": [
    {
      "text": "Me at the zoo is the first video on YouTube...",
      "chunk_id": 0,
      "source": "jNQXAC9IVRw"
    }
  ],
  "verification": {
    "is_grounded": true,
    "has_hallucinations": false,
    "is_relevant": true,
    "confidence": 0.92,
    "explanation": "Answer is directly from the transcript"
  },
  "confidence": 0.92
}
```

### Query Quality Tips

```bash
# ✓ Good: Specific questions
"What specific examples are mentioned?"

# ✓ Good: Reference-based questions
"What is said about technology?"

# ✓ Good: Sequential questions
"What happens after the introduction?"

# ✗ Avoid: Vague questions
"Tell me about everything"

# ✗ Avoid: Opinion questions
"Is this video good?"

# ✗ Avoid: Out-of-scope questions
"What's happening outside the video?"
```

---

## 4. Get Chat History

**Retrieve all messages in a session**

```bash
curl http://localhost:8000/api/chat_history/jNQXAC9IVRw
```

**Response:**
```json
[
  {
    "role": "user",
    "content": "What is the main topic?",
    "timestamp": "2024-03-18T10:30:15.000000"
  },
  {
    "role": "assistant",
    "content": "The main topic is...",
    "timestamp": "2024-03-18T10:30:20.000000"
  }
]
```

---

## 5. List All Sessions

**Get all active sessions**

```bash
curl http://localhost:8000/api/sessions
```

**Response:**
```json
[
  {
    "session_id": "jNQXAC9IVRw",
    "video_id": "jNQXAC9IVRw",
    "created_at": "2024-03-18T10:30:00.000000",
    "messages_count": 4
  }
]
```

---

## 6. Delete Session

**Remove a session and its history**

```bash
curl -X DELETE http://localhost:8000/api/sessions/jNQXAC9IVRw
```

**Response:**
```json
{
  "status": "deleted",
  "session_id": "jNQXAC9IVRw"
}
```

---

## 7. Clear All Data

**Clear all sessions and embeddings (USE WITH CAUTION)**

```bash
curl -X POST http://localhost:8000/api/clear_all
```

**Response:**
```json
{
  "status": "cleared",
  "message": "All sessions and index cleared"
}
```

---

## 🐍 Python Testing Script

Save as `test_api.py`:

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✓ Health check passed\n")

def test_process_video():
    """Process a video."""
    print("Processing video...")
    data = {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "languages": ["en"]
    }
    response = requests.post(f"{BASE_URL}/api/process_video", json=data)
    assert response.status_code == 200
    result = response.json()
    video_id = result["video_id"]
    print(f"✓ Video {video_id} processing started")
    print(f"  Chunks: {result['chunks_count']}\n")
    
    # Wait for processing
    print("Waiting for processing to complete (this can take a minute)...")
    time.sleep(60)  # Wait 60 seconds
    print("✓ Ready for queries\n")
    
    return video_id

def test_chat(session_id):
    """Test chat query."""
    print(f"Testing chat query...")
    data = {
        "session_id": session_id,
        "query": "What is the main topic of this video?"
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=data)
    assert response.status_code == 200
    result = response.json()
    
    print(f"Question: {data['query']}")
    print(f"Answer: {result['answer'][:200]}...\n")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Grounded: {result['verification']['is_grounded']}")
    print(f"Hallucinations: {result['verification']['has_hallucinations']}\n")
    
    # Test another question
    data["query"] = "Can you provide more details?"
    response = requests.post(f"{BASE_URL}/api/chat", json=data)
    print("✓ Second query successful\n")

def test_history(session_id):
    """Test getting chat history."""
    print(f"Getting chat history...")
    response = requests.get(f"{BASE_URL}/api/chat_history/{session_id}")
    assert response.status_code == 200
    history = response.json()
    print(f"✓ Retrieved {len(history)} messages\n")

def test_sessions():
    """Test listing sessions."""
    print("Listing all sessions...")
    response = requests.get(f"{BASE_URL}/api/sessions")
    assert response.status_code == 200
    sessions = response.json()
    print(f"✓ Found {len(sessions)} session(s)\n")

def main():
    print("=" * 60)
    print("Video RAG API Testing")
    print("=" * 60 + "\n")
    
    try:
        # Test health
        test_health()
        
        # Process video
        video_id = test_process_video()
        
        # Test chat
        test_chat(video_id)
        
        # Test history
        test_history(video_id)
        
        # Test sessions
        test_sessions()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        print("\nMake sure:")
        print("1. Backend is running on http://localhost:8000")
        print("2. OPENAI_API_KEY is set correctly")
        print("3. Internet connection is available")

if __name__ == "__main__":
    main()
```

**Run the test:**

```bash
python test_api.py
```

---

## 🔍 Interactive API Documentation

FastAPI provides automatic interactive documentation:

```
http://localhost:8000/docs          # Swagger UI (recommended)
http://localhost:8000/redoc         # ReDoc
```

Visit these URLs to:
- See all endpoints
- View request/response schemas
- Try endpoints directly in browser
- Get auto-complete for parameters

---

## ⚠️ Error Responses

### 400 - Bad Request

```json
{
  "detail": "Invalid YouTube URL or video ID"
}
```

**Fix:** Verify the video URL is correct

### 404 - Not Found

```json
{
  "detail": "Session xyz not found"
}
```

**Fix:** Process a video first or use correct session ID

### 500 - Server Error

```json
{
  "detail": "Error processing query: [error message]"
}
```

**Fix:** Check backend logs, verify API key, restart backend if needed

---

## 📊 Response Time Benchmarks

Typical times on standard hardware:

| Operation | Time |
|-----------|------|
| Process 10-min video | 30-60s |
| First query | 3-8s |
| Verification | 2-5s |
| Subsequent queries | 2-5s |
| Chat history retrieval | <500ms |

*Times vary based on video length, chunk size, and model selection*

---

## 🧪 Batch Testing

Process multiple videos:

```bash
#!/bin/bash

VIDEOS=(
  "https://www.youtube.com/watch?v=jNQXAC9IVRw"
  "https://www.youtube.com/watch?v=VIDEO_ID_2"
  "https://www.youtube.com/watch?v=VIDEO_ID_3"
)

for video in "${VIDEOS[@]}"; do
  echo "Processing: $video"
  curl -X POST http://localhost:8000/api/process_video \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$video\", \"languages\": [\"en\"]}"
  sleep 5
done
```

---

## 🔐 Production Testing

Before deployment:

```bash
# Test with invalid inputs
curl -X POST http://localhost:8000/api/process_video \
  -H "Content-Type: application/json" \
  -d '{"url": "invalid-url", "languages": []}'

# Test with empty query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xyz", "query": ""}'

# Test concurrent requests (use Apache Bench)
ab -n 10 -c 5 http://localhost:8000/health
```

---

**Happy testing! 🚀**
