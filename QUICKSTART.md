# 🚀 Quick Start Guide

Get the Video RAG application running in **5 minutes**!

## Step 1: Clone/Navigate to Project

```bash
cd d:\VideoRAGExample
```

## Step 2: Activate Virtual Environment

```bash
# Windows
ragEnv\Scripts\activate

# macOS/Linux
source ragEnv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Set Up Environment Variables

```bash
# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-your-api-key-from-openai-here"

# Or create .env file:
# OPENAI_API_KEY=sk-your-api-key
```

**Get API Key:**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (save it somewhere safe!)

## Step 5: Start FastAPI Backend

In **Terminal/PowerShell 1**:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

## Step 6: Start Streamlit Frontend

In **Terminal/PowerShell 2**:

```bash
streamlit run frontend/app.py
```

The browser will auto-open to `http://localhost:8501`

## Step 7: Use the App

1. **Paste YouTube URL:**
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **Click "Process Video"** (wait 30-60 seconds)

3. **Ask Questions:**
   ```
   "What is the main topic of this video?"
   ```

4. **Get AI-Generated Answer** with sources and verification!

---

## 🎯 Test with Sample Videos

### Short Videos (Fastest)
- TED Talk clips (5-10 minutes)
- YouTube Shorts
- Music videos

### Medium Videos (Recommended)
- Tutorials (10-30 minutes)
- News segments (10-20 minutes)
- Podcasts (standard length)

### Full Videos (Will work, takes longer)
- Documentaries
- Full lectures
- Long-form content

---

## ✅ Verification Checklist

### After starting Backend:
```
✓ Terminal shows "Uvicorn running on http://0.0.0.0:8000"
✓ No error messages
✓ You can visit http://localhost:8000/docs (API documentation)
```

### After starting Frontend:
```
✓ Browser opens to http://localhost:8501
✓ Streamlit logo appears in top-right
✓ No error messages in terminal
✓ "✅ API Connected" message appears
```

### Test API Health (optional):
```bash
# In new terminal
curl http://localhost:8000/health
```

---

## 🆘 Quick Troubleshooting

### "Module not found" Error

```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt

# Or install specific package
pip install openai langchain faiss-cpu
```

### "API not running"

```bash
# Terminal 1 - make sure it's still running
# If not, start it again:
python -m uvicorn backend.main:app --reload
```

### "Invalid OpenAI API Key"

```bash
# Verify key is set:
echo $env:OPENAI_API_KEY  # Should show "sk-..."

# If empty, set it:
$env:OPENAI_API_KEY = "sk-your-real-key"
```

### Video Not Processing

- Check internet connection
- Verify YouTube URL is correct and public
- Try a different video
- Check if transcript is available (most videos have it)

---

## 📚 Next Steps

1. **Read Full Documentation:**
   - See `README.md` for comprehensive guide

2. **Try Different Videos:**
   - Educational content works best
   - Videos with clear transcripts preferred

3. **Explore API:**
   - Visit `http://localhost:8000/docs` for interactive API explorer

4. **Ask Better Questions:**
   - Specific questions work better
   - Reference timestamps when possible

5. **Customize Settings:**
   - See `config/settings.py` for advanced options

---

## 💡 Pro Tips

- **GPU Available?** Install `faiss-gpu` for faster searches
- **Want Faster Responses?** Use `gpt-3.5-turbo` in config
- **Multiple Videos?** Clear session between videos (button in sidebar)
- **Debugging?** Check terminal logs for detailed error messages

---

## 🎬 Next Video to Try

Great starter videos:
- Any TED talk (usually 15-20 minutes)
- Technical tutorial on a specific topic
- News from a reputable source
- Educational content

---

Ready to go? Start with **Step 1** above! 🚀

Having issues? Check **Troubleshooting** section or see `README.md` for detailed help.
