import streamlit as st
import warnings
warnings.filterwarnings("ignore")
import streamlit as st
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI
# RetrievalQA/ConversationalRetrievalChain import removed due to missing module     in this Langchain version
import re
import webbrowser

# Helper to extract YouTube video ID
def extract_video_id(url):
    match = re.search(r"(?:v=|youtu.be/)([\w-]+)", url)
    return match.group(1) if match else None

# Helper to get transcript
def get_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        # transcript: list of dicts with 'text', 'start', 'duration'
        return transcript
    except Exception as e:
        import streamlit as st
        st.error(f"YouTubeTranscriptApi error: {e}")
        return []

# Helper to chunk transcript and keep time references
def chunk_transcript(transcript, chunk_size=500):
    chunks = []
    current = ""
    start_time = None
    for entry in transcript:
        # Support both dict and object
        start = entry['start'] if isinstance(entry, dict) else getattr(entry, 'start', 0)
        text = entry['text'] if isinstance(entry, dict) else getattr(entry, 'text', '')
        if not current:
            start_time = start
        current += text + " "
        if len(current) > chunk_size:
            chunks.append({'text': current.strip(), 'start': start_time})
            current = ""
    if current:
        chunks.append({'text': current.strip(), 'start': start_time})
    return chunks

# Helper to format seconds to mm:ss
def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

# Streamlit UI
st.title("YouTube Video Q&A Chat")
st.write("Paste a YouTube link, ask questions about the video content, and get answers with reference timeframes.")

with open("openai_key.txt") as f:
    openai_api_key = f.read().strip()
st.write('DEBUG: openai_api_key:', openai_api_key)

youtube_url = st.text_input("Paste YouTube video link")

if youtube_url:
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.error("Invalid YouTube link.")
    else:
        st.info("Fetching transcript...")
        try:
            transcript = get_transcript(video_id)
            st.success("Transcript loaded.")
            # Chunk transcript
            chunks = chunk_transcript(transcript)
            texts = [str(c['text']) for c in chunks if isinstance(c, dict) and 'text' in c]
            texts = [t for t in texts if t and t.strip()]
            st.write('DEBUG: filtered texts:', texts)
            # Minimal FAISS test block
            try:
                test_texts = ["hello world", "foo bar", "baz qux"]
                test_embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
                test_vectorstore = FAISS.from_texts(test_texts, test_embeddings)
                st.write('DEBUG: Minimal FAISS test succeeded.')
            except Exception as e:
                st.error(f"Minimal FAISS test error: {e}")
            st.write('DEBUG: types in texts:', [type(t) for t in texts])
            # Ensure all metadata values are simple types
            metadatas = []
            for c in chunks:
                start = c['start'] if isinstance(c, dict) else getattr(c, 'start', 0)
                if isinstance(start, (int, float, str)):
                    metadatas.append({'start': start})
                else:
                    metadatas.append({'start': str(start)})
            st.write('DEBUG: metadatas:', metadatas)
            # Embedding and vector store
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            st.write('DEBUG: embeddings type:', type(embeddings))
            st.write('DEBUG: sample text:', texts[:2])
            st.write('DEBUG: sample metadata:', metadatas[:2])
            import traceback
            st.write('DEBUG: len(texts):', len(texts))
            st.write('DEBUG: len(metadatas):', len(metadatas))
            st.write('DEBUG: texts:', texts)
            st.write('DEBUG: metadatas:', metadatas)
            try:
                vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
            except Exception as e:
                st.error(f"FAISS.from_texts error: {e}\n" + traceback.format_exc())
                st.write('DEBUG: Retrying FAISS.from_texts without metadatas...')
                try:
                    vectorstore = FAISS.from_texts(texts, embeddings)
                except Exception as e2:
                    st.error(f"FAISS.from_texts (no metadatas) error: {e2}\n" + traceback.format_exc())
                    raise
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
            llm = OpenAI(openai_api_key=openai_api_key, temperature=0.2)
            question = st.text_input("Ask a question about the video:")
            if question:
                with st.spinner("Thinking..."):
                    # Retrieve relevant docs
                    docs = retriever.invoke({"query": question})
                    st.write('DEBUG: docs:', docs)
                    st.write('DEBUG: types in docs:', [type(doc) for doc in docs])
                    # Compose a context for the LLM
                    context = "\n\n".join([
                        doc.page_content if hasattr(doc, 'page_content') else str(doc)
                        for doc in docs
                    ])
                    st.write('DEBUG: context for LLM:', context)
                    prompt = f"Answer the question in simple English using only the context below.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
                    answer = llm.invoke(prompt)
                st.markdown(f"**Answer:** {answer}")
                st.markdown("---")
                st.markdown("**Reference Timeframes:**")
                found_time = False
                for doc in docs:
                    if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                        start = doc.metadata.get('start', 0)
                        time_str = format_time(start)
                        url_with_time = f"https://www.youtube.com/watch?v={video_id}&t={int(start)}s"
                        st.markdown(f"[{time_str}]({url_with_time})", unsafe_allow_html=True)
                        found_time = True
                if not found_time:
                    st.info("No reference timeframes available for this answer.")
        except Exception as e:
            st.error(f"Error: {e}")
