# Video RAG: Advanced YouTube Q&A with Answer Verification

A production-ready web application that enables users to interact with YouTube videos through an advanced **Retrieval-Augmented Generation (RAG)** pipeline with answer verification to reduce hallucinations.

<img width="917" height="455" alt="image" src="https://github.com/user-attachments/assets/e990a2f1-8c21-4dd8-8972-8ded3b906941" />


## 🎯 Overview

This application combines:
- **YouTube Processing**: Extract transcripts from any YouTube video
- **Vector Embeddings**: Convert text into semantic embeddings using OpenAI
- **FAISS Vector Store**: Efficiently retrieve relevant content
- **RAG Pipeline**: Retrieve context, re-rank, generate answers, and verify correctness
- **Answer Verification**: Detect and mitigate hallucinations using a verification LLM
- **Web Interface**: Streamlit frontend + FastAPI backend

### Key Features

✅ **Smart Video Processing**
- Automatic transcript extraction from YouTube URLs
- Support for multiple languages
- Intelligent text chunking with semantic boundaries

✅ **Advanced RAG Pipeline**
- Semantic retrieval from FAISS vector store
- Result re-ranking for better relevance
- LLM-based answer generation with context
- **Answer verification** to detect hallucinations
- Confidence scoring for each answer

✅ **Production-Ready**
- RESTful API with FastAPI
- Session-based chat management
- Comprehensive error handling
- Environment-based configuration
- Security best practices

✅ **User-Friendly Interface**
- Clean Streamlit chat UI
- Real-time answer verification display
- Source chunk references
- Confidence score visualization

---

## 🏗️ Architecture

### High-Level Flow

```
YouTube URL
    ↓
Extract Transcript (YouTubeTranscriptAPI)
    ↓
Preprocess & Chunk Text (RecursiveCharacterTextSplitter)
    ↓
Create Embeddings (OpenAI Embeddings API)
    ↓
Store in FAISS Vector Store
    ↓
User Query
    ↓
Retrieve Top-K Chunks (FAISS Search)
    ↓
Re-rank Results (Relevance Scoring)
    ↓
Generate Answer (GPT-4 with Context)
    ↓
Verify Answer (Verification LLM)
    ↓
Apply Confidence Threshold
    ↓
Return Answer + Sources + Verification
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                      │
│  - Video URL Input                                           │
│  - Chat Interface                                            │
│  - Answer Display with Verification                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                            │
│  - Video Processing Endpoint                                 │
│  - Chat Query Endpoint                                       │
│  - Session Management                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    ┌────────┐  ┌─────────┐  ┌─────────────┐
    │ RAG    │  │OpenAI   │  │ FAISS       │
    │Pipeline│  │API      │  │Vector Store │
    └────────┘  └─────────┘  └─────────────┘
```

### Folder Structure

```
VideoRAGExample/
├── backend/                    # FastAPI application
│   └── main.py               # Main API endpoints
├── frontend/                   # Streamlit application
│   ├── app.py                # Main Streamlit interface
│   └── .streamlit/            # Streamlit configuration
│       ├── config.toml
│       └── secrets.toml
├── rag/                        # RAG implementation
│   ├── embeddings.py         # FAISS embeddings manager
│   └── pipeline.py           # RAG pipeline with verification
├── config/
│   └── settings.py           # Configuration management
├── utils/
│   ├── youtube_utils.py      # YouTube processing
│   └── text_processing.py    # Text chunking & preprocessing
├── data/                       # Data directory
│   ├── faiss_index           # FAISS index file
│   └── metadata.pkl          # Chunk metadata
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment file
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- 2GB+ disk space for embeddings
- Internet connection

### Installation

#### 1. **Clone or Setup Project**

```bash
cd d:\VideoRAGExample
```

#### 2. **Create Virtual Environment**

```bash
# Windows
python -m venv ragEnv
ragEnv\Scripts\activate

# macOS/Linux
python -m venv ragEnv
source ragEnv/bin/activate
```

#### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

#### 4. **Setup Environment Variables**

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your OpenAI API key
# Windows Users: Use Notepad or your preferred editor
$env:OPENAI_API_KEY = "your-api-key-here"
```

Or create `.env` file manually with:

```env
OPENAI_API_KEY=sk-your_openai_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
```

#### 5. **Create Streamlit Secrets** (Optional but Recommended)

Create `.streamlit/secrets.toml`:

```toml
api_url = "http://localhost:8000"
```

---

## 🎮 Running the Application

### Option 1: Run Backend and Frontend Separately

#### Terminal 1 - Start FastAPI Backend

```bash
# Make sure your virtual environment is active
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2 - Start Streamlit Frontend

```bash
streamlit run frontend/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### Option 2: Run Both with One Command (Development)

```bash
# In PowerShell
$backend = Start-Job -ScriptBlock { python -m uvicorn backend.main:app --reload }
Start-Sleep -Seconds 3
streamlit run frontend/app.py

# Stop the backend later with:
# Stop-Job -Job $backend
```

---

## 📊 Usage Example

### Step 1: Open the Application

Navigate to `http://localhost:8501` in your browser.

### Step 2: Process a YouTube Video

1. Paste a YouTube URL in the sidebar:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
   Or just the video ID: `dQw4w9WgXcQ`

2. Select languages (default: English)

3. Click **"🚀 Process Video"**

Wait for the confirmation:
```
✅ Video processed!

Video ID: dQw4w9WgXcQ
Chunks: 45
```

### Step 3: Ask Questions

Once the video is processed, type your question:

```
"What is the main topic of this video?"
```

### Step 4: Receive Answer with Verification

The system returns:

```
📝 Answer:
The video discusses [main topic]...

📊 Answer Confidence: 85%

📊 Answer Verification Details:
- Confidence: 0.85
- Grounded in Context: ✓ Yes
- Hallucinations: ✗ None
- Relevant: ✓ Yes

📚 Source Chunks:
[Retrieved context excerpts]
```

---

## 🔧 API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Video RAG API",
  "timestamp": "2024-03-18T10:30:00"
}
```

### Process Video

```bash
POST /api/process_video
```

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "languages": ["en"]
}
```

**Response:**
```json
{
  "status": "processing",
  "message": "Video VIDEO_ID is being processed",
  "video_id": "VIDEO_ID",
  "chunks_count": 45
}
```

### Chat Query

```bash
POST /api/chat
```

**Request:**
```json
{
  "session_id": "VIDEO_ID",
  "query": "What is the main topic?"
}
```

**Response:**
```json
{
  "answer": "The main topic is...",
  "sources": [
    {
      "text": "Context excerpt...",
      "chunk_id": 0,
      "source": "transcript"
    }
  ],
  "verification": {
    "is_grounded": true,
    "has_hallucinations": false,
    "is_relevant": true,
    "confidence": 0.85,
    "explanation": "Answer is direct quote from transcript"
  },
  "confidence": 0.85
}
```

### Get Chat History

```bash
GET /api/chat_history/{session_id}
```

### List Sessions

```bash
GET /api/sessions
```

### Delete Session

```bash
DELETE /api/sessions/{session_id}
```

### Clear All Data

```bash
POST /api/clear_all
```

---

## 🧠 RAG Pipeline Details

### 1. **Retrieval**

- User query is converted to embedding using OpenAI's embedding model
- FAISS performs L2-distance search to find top-k similar chunks
- Results sorted by semantic similarity

```python
retrieved_chunks = rag_pipeline.retrieve(query, k=5)
```

### 2. **Re-ranking** (Optional but Recommended)

- Re-rank chunks based on:
  - Query term overlap
  - Original similarity score
  - Combined relevance scoring

Improves quality by prioritizing most relevant chunks.

### 3. **Generation**

- Retrieved context is formatted with chunk delimiters
- GPT-4 (or specified model) generates answer using context
- System prompt ensures answers are grounded in context

### 4. **Verification** (Unique Feature!)

Answer is verified against context using a separate LLM call:

```
Is the answer grounded in context?
Does it contain hallucinations?
Is it relevant to the query?
Confidence score 0-1?
```

### 5. **Confidence Threshold**

If confidence < 0.7 (configurable):
```
"I'm not confident in my answer. Based on the video, 
I cannot provide a reliable response to your question."
```

**Benefits:**
- ✅ Reduces false information
- ✅ User knows when to trust the answer
- ✅ Prevents confident hallucinations

---

## ⚙️ Configuration

All settings are in `config/settings.py`:

```python
# RAG Settings
chunk_size: int = 1000              # Characters per chunk
chunk_overlap: int = 200            # Overlap between chunks
max_retrieved_chunks: int = 5       # Top-k to retrieve
confidence_threshold: float = 0.7   # Min confidence to return

# Model Selection
openai_model: str = "gpt-4.1-mini-2025-04-14"
openai_model_verification: str = "gpt-3.5-turbo"

# Processing
youtube_timeout: int = 30
embedding_batch_size: int = 10
```

### Customizing Settings

Edit these values in `config/settings.py` or via environment variables:

```bash
# Increase chunk size for longer context
$env:CHUNK_SIZE = "1500"

# Use GPT-3.5 for answers (faster, cheaper)
$env:OPENAI_MODEL = "gpt-3.5-turbo"

# Increase confidence threshold (stricter answers)
$env:CONFIDENCE_THRESHOLD = "0.8"
```

---

## 🔒 Security Best Practices

✅ **Implemented:**
- API key stored in `.env` file (never hardcoded)
- Environment variables loaded via python-dotenv
- `.env` added to `.gitignore`
- No sensitive data in logs

✅ **Recommended for Production:**
- Use environment variables from secure vaults (AWS Secrets Manager, Azure KeyVault)
- Add authentication to FastAPI endpoints
- Use HTTPS for API communication
- Rate limiting on endpoints
- Input validation and sanitization

---

## 📈 Performance Optimization

### Tips for Better Performance

1. **Reduce Chunk Size** for faster retrieval:
   ```python
   chunk_size=500  # Default is 1000
   ```

2. **Use CPU-optimized FAISS**:
   Already using `faiss-cpu` by default

3. **Cache Embeddings**:
   Embeddings are saved to disk and reused

4. **Batch Processing**:
   Use `embedding_batch_size` in config

5. **Model Selection**:
   - Use `gpt-3.5-turbo` for faster responses
   - Use `gpt-4` for higher quality

### Costs

Approximate costs per video (varies by length):

- **Extracting Transcript**: Free (YouTube API)
- **Creating Embeddings**: ~$0.02 (10K words @ ~$2/1M tokens)
- **Generating Answers**: ~$0.01-0.05 per query (GPT model dependent)
- **Verification**: ~$0.005 per query

---

## 🧪 Sample Test Queries

Try these questions on any video:

```
1. "What is the main topic of this video?"
2. "What are the key takeaways?"
3. "Can you summarize the video?"
4. "What specific points are mentioned about [topic]?"
5. "Who are the main speakers or characters?"
6. "What examples are given?"
7. "What is the first thing mentioned?"
8. "Are there any statistics or numbers mentioned?"
9. "What is the conclusion of the video?"
10. "How long is the video?"
```

---

## 🚨 Troubleshooting

### "API is not running"

**Solution:**
```bash
# In Terminal 1:
python -m uvicorn backend.main:app --reload
```

### "No transcript found"

**Causes:**
- Video has transcripts disabled
- Language not available
- Invalid video ID

**Solution:**
- Verify video URL is correct
- Check if transcript is available on YouTube
- Try different language

### Out of Memory Error

**Solution:**
- Reduce `chunk_size` in config
- Use `faiss-gpu` if GPU available
- Reduce `max_retrieved_chunks`

### Slow Response Times

**Solution:**
- Use `gpt-3.5-turbo` instead of `gpt-4`
- Reduce `chunk_size`
- Increase `max_retrieved_chunks` gradually

### "Invalid OpenAI API Key"

**Solution:**
```bash
# Verify .env file:
cat .env

# Key should be: sk-...
# If blank, set it:
$env:OPENAI_API_KEY = "sk-your-key"
```

---

## 🔄 Workflow Diagram

```
User Input (YouTube URL)
        ↓
    FastAPI Endpoint
        ↓
    Extract Video ID
        ↓
    Get Transcript (YouTubeTranscriptAPI)
        ↓
    Preprocess & Chunk Text
        ↓
    Create Embeddings (OpenAI)
        ↓
    Build FAISS Index
        ↓
    Save to Disk
        ↓
    [READY FOR QUERIES]
        ↓
    User Query
        ↓
    Convert to Embedding
        ↓
    Search FAISS Index
        ↓
    Re-rank Results
        ↓
    Generate Answer (LLM)
        ↓
    Verify Answer (Verification LLM)
        ↓
    Check Confidence Threshold
        ↓
    Return Answer + Sources + Verification
        ↓
    Display in Streamlit UI
```

---

## 📦 Dependencies

Key packages used:

```
langchain>=0.1.0              # LLM framework
openai>=1.3.0                 # OpenAI API
youtube-transcript-api>=0.6.1 # YouTube transcripts
faiss-cpu>=1.7.4              # Vector search
fastapi>=0.104.0              # Backend API
streamlit>=1.28.0             # Frontend
```

See `requirements.txt` for complete list.

---

## 🎯 Future Improvements

### Planned Features

- [ ] **Multi-video Comparison**: Compare content across videos
- [ ] **Conversation Memory**: Better context in multi-turn conversations
- [ ] **Video Summarization**: Auto-generate summaries
- [ ] **Transcript Editing**: Allow users to refine transcripts
- [ ] **Citation Generation**: Automatic citations with timestamps
- [ ] **Database Backend**: Replace in-memory sessions with DB
- [ ] **Authentication**: User accounts and history
- [ ] **Video Preview**: Embedded video player in Streamlit
- [ ] **Advanced RAG**: Different re-ranking strategies
- [ ] **Fine-tuning**: Custom models on user data

### Performance Improvements

- [ ] Async embeddings generation
- [ ] Redis caching for embeddings
- [ ] GPU acceleration for FAISS
- [ ] Implement streaming responses
- [ ] Multi-worker deployment

### Robustness

- [ ] Better error handling
- [ ] Detailed logging
- [ ] Monitoring and metrics
- [ ] Tests (unit, integration, e2e)
- [ ] Input validation improvements
- [ ] Rate limiting

---

## 📝 Example Use Cases

### 1. **Educational Content Analysis**
Process lecture videos and ask questions about concepts covered.

### 2. **Content Research**
Extract key information from interviews and documentaries.

### 3. **Meeting/Webinar Recap**
Record, upload, and query important meetings.

### 4. **News Monitoring**
Stay informed about specific topics across multiple videos.

### 5. **Language Learning**
Learn from videos by asking comprehension questions.

---

## 🤝 Contributing

Contributions welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 📧 Support

For issues and questions:

1. Check the **Troubleshooting** section above
2. Review **Sample Test Queries** for expected behavior
3. Check API logs in terminal for errors
4. Verify environment setup

---

## 🎓 Learning Resources

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FAISS Documentation](https://faiss.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs)

---

**Happy Querying! 🚀**
