import streamlit as st
import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone

# Load .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# ✅ Init Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "chatbot-index"

# ✅ Setup embeddings (HuggingFace MiniLM, 384 dims → matches index)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ✅ Connect to Pinecone vectorstore
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

# ✅ Setup Groq LLM
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model=MODEL,
    temperature=0
)

# ✅ Custom prompt (forces use of context only)
QA_PROMPT = PromptTemplate(
    template="""
You are a helpful assistant. 
Use ONLY the following context from the PDF to answer the question. 
If the answer is not in the context, just say: "I don’t know based on the document."

Context:
{context}

Question: {question}
Answer:
""",
    input_variables=["context", "question"],
)

# ✅ Setup RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type="stuff",
    chain_type_kwargs={"prompt": QA_PROMPT},
    return_source_documents=True
)

# Streamlit UI
st.set_page_config(page_title="📄 PDF Chatbot (Groq + Pinecone)", layout="wide")
st.title("📄 PDF-based Chatbot with Pinecone (`chatbot-index`) + Groq")

uploaded_file = st.file_uploader("📤 Upload a PDF", type="pdf")

if uploaded_file is not None:
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text()

    # Split into chunks
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    # Store chunks in Pinecone index
    if chunks:
        vectorstore.add_texts(chunks)
        st.success("✅ PDF uploaded and indexed into 'chatbot-index'!")
    else:
        st.warning("⚠️ No text found in the uploaded PDF.")

# Chat input
query = st.text_input("💬 Ask a question about the PDF:")

if query:
    result = qa_chain({"query": query})

    st.markdown("### 🤖 Chatbot Response")
    st.write(result["result"])

    # Show retrieved chunks clearly
    st.markdown("### 📑 Retrieved Chunks from PDF")
    for i, doc in enumerate(result["source_documents"], start=1):
        st.markdown(f"**Chunk {i}:**")
        st.write(doc.page_content.strip()[:1000])  # display up to 1000 chars
        st.markdown("---")
