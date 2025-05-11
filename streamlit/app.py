import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Adjust these if your API runs elsewhere
API_BASE = os.getenv("BACKEND_PATH")

st.set_page_config(page_title="RAG Chatbot", layout="wide")

# --- Sidebar: File upload + Settings ---
st.sidebar.header("📚 Upload Knowledge")
uploaded = st.sidebar.file_uploader(
    "Choose a file (.pdf, .txt, .docx)",
    type=["pdf", "txt", "docx"]
)
username = st.sidebar.text_input("Username", value="guest")

# Number of chunks
num_chunks = st.sidebar.slider(
    "Number of Chunks",
    min_value=1,
    max_value=20,
    value=5,
    step=1
)

# New: Retrieval mode selector
mode = st.sidebar.selectbox(
    "Retrieval Mode",
    options=["dense", "sparse", "hybrid"],
    index=0,
    help="dense = vector only; sparse = BM25 only; hybrid = both"
)

# New: Score threshold slider
score_threshold = st.sidebar.slider(
    "Score Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.2,
    step=0.01,
    help="Minimum similarity score (0–1) to filter out low-relevance results"
)

if st.sidebar.button("📥 Index Document"):
    if not uploaded:
        st.sidebar.error("Please select a file first.")
    else:
        with st.spinner("Indexing…"):
            files = {"file": (uploaded.name, uploaded.getvalue())}
            data = {"username": username}
            resp = requests.post(f"{API_BASE}/upload-knowledge", files=files, data=data)
        if resp.status_code == 200:
            st.sidebar.success("Indexed successfully!")
            st.sidebar.write(resp.json().get("extracted_text", "")[:200] + "…")
        else:
            st.sidebar.error(f"Error: {resp.text}")

# --- Main: Chat interface ---
st.title("🤖 Retrieval-Augmented Chatbot")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "history" not in st.session_state:
    st.session_state.history = []

# Render past messages
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask me anything"):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build request payload
    params = {
        "username": username,
        "query": prompt,
        "session_id": st.session_state.session_id or "",
        "no_of_chunks": num_chunks,
        "mode": mode,                       
        "score_threshold": score_threshold
    }

    with st.chat_message("assistant"):
        message_holder = st.empty()
        partial = ""
        try:
            resp = requests.post(
                f"{API_BASE}/chat_stream",
                json=params,
                stream=True,
                headers={"Accept": "application/x-ndjson"},
            )
            if resp.status_code != 200:
                message_holder.markdown(f"**Error:** {resp.text}")
            else:
                for line in resp.iter_lines(decode_unicode=True):
                    if line:
                        data = json.loads(line)
                        if "session_id" in data:
                            st.session_state.session_id = data["session_id"]
                        elif "chunk" in data:
                            partial += data["chunk"]
                            message_holder.markdown(partial)
                        # ignore other control messages
        except Exception as e:
            message_holder.markdown(f"**Error:** {e}")

    st.session_state.history.append({"role": "assistant", "content": partial})
