import os
import time
import streamlit as st
from groq import Groq
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ----------------------------
# Load environment
# ----------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
INDEX_NAME = os.getenv("INDEX_NAME", "chatbot-index")

# ----------------------------
# Groq client
# ----------------------------
groq_client = Groq(api_key=GROQ_API_KEY)

# ----------------------------
# Pinecone init
# ----------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
    )
index = pc.Index(INDEX_NAME)

# ----------------------------
# Embeddings
# ----------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Groq + Pinecone Chatbot", page_icon="🤖", layout="wide")

# Inject CSS
with open("assets/bg.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <h1 style="text-align:center; color:#1abc9c;">✨ Creative AI Chatbot ✨</h1>
    <p style="text-align:center; color:#bdc3c7;">Powered by <b>Groq + Pinecone</b></p>
    """,
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.title("⚙️ Settings")
user_id = st.sidebar.text_input("User ID", value="user1")
clear_chat = st.sidebar.button("Clear Chat")

if clear_chat:
    st.session_state["messages"] = []
    st.sidebar.success("Chat cleared!")

# Messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display history
for msg in st.session_state["messages"]:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Type your message..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Store in Pinecone
    ts = str(time.time())
    vec = embedder.encode([prompt]).tolist()[0]
    index.upsert(
        vectors=[
            {
                "id": f"{user_id}-{ts}",
                "values": vec,
                "metadata": {"user": user_id, "text": prompt, "timestamp": ts},
            }
        ]
    )

    # Search past context
    query_emb = embedder.encode([prompt]).tolist()[0]
    results = index.query(vector=query_emb, top_k=3, include_metadata=True)
    context = "\n".join([m["metadata"]["text"] for m in results.get("matches", [])])

    # Groq response
    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        response_text = ""

        messages = [
            {"role": "system", "content": "You are a creative helpful assistant."},
            {"role": "system", "content": f"Relevant past context:\n{context}"},
        ] + st.session_state["messages"]

        stream = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            response_text += delta
            msg_placeholder.markdown(response_text + "▌")

        msg_placeholder.markdown(response_text)

    st.session_state["messages"].append({"role": "assistant", "content": response_text})
