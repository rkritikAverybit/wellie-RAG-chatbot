import streamlit as st
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv
from io import BytesIO
from pypdf import PdfReader
from docx import Document
import os
import tiktoken

# ========== BASIC CONFIG ==========
st.set_page_config(page_title="📘 Wellie Knowledge Admin", page_icon="📘", layout="wide")
load_dotenv()

# ---- Simple Admin Password Gate ----
password = st.text_input("Enter admin password:", type="password")
if password != os.getenv("ADMIN_PASSWORD", "wellie123"):
    st.warning("🔒 Access restricted. Please enter the correct admin password.")
    st.stop()

# ========== ENVIRONMENT VARIABLES ==========
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not OPENAI_API_KEY:
    st.error("Missing environment variables. Please check your .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
enc = tiktoken.get_encoding("cl100k_base")

# ========== HELPER FUNCTIONS ==========
def extract_text(file) -> str:
    name = file.name.lower()
    data = file.read()
    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif name.endswith(".docx"):
        doc = Document(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs])
    elif name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    else:
        return ""

def chunk_text(text: str, chunk_size=800, overlap=100):
    tokens = enc.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = tokens[i:i + chunk_size]
        chunks.append(enc.decode(chunk))
        i += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]

def upload_to_supabase(source, text, lang="en"):
    chunks = chunk_text(text)
    embeddings = client.embeddings.create(model="text-embedding-3-large", input=chunks)
    vectors = [e.embedding for e in embeddings.data]

    rows = []
    for i, (c, v) in enumerate(zip(chunks, vectors)):
        rows.append({
            "source": source,
            "section": f"{source}_part_{i+1}",
            "content": c,
            "embedding": v,
            "metadata": {"lang": lang}
        })

    batch_size = 100
    for i in range(0, len(rows), batch_size):
        supabase.table("spiritual_knowledge").upsert(rows[i:i + batch_size]).execute()

    return len(rows)

# ========== MAIN UI ==========
st.title("📘 Wellie Knowledge Admin Panel")

tab1, tab2 = st.tabs(["📤 Upload Document", "🗂 Manage Documents"])

# ---- Upload Tab ----
with tab1:
    st.subheader("Upload a Document to Supabase Vector DB")
    source = st.text_input("Source name (unique identifier)", placeholder="e.g. mindfulness_basics")
    lang = st.text_input("Language (ISO code)", value="en")
    file = st.file_uploader("Choose a document", type=["pdf", "docx", "txt"])

    if st.button("Upload"):
        if not source or not file:
            st.warning("Please enter a source name and select a file.")
        else:
            with st.spinner("Extracting text..."):
                text = extract_text(file)
            if not text.strip():
                st.error("No readable text found in the file.")
            else:
                with st.spinner("Generating embeddings and uploading..."):
                    count = upload_to_supabase(source, text, lang)
                st.success(f"✅ Uploaded {count} chunks from '{source}' successfully!")

# ---- Manage Tab ----
with tab2:
    st.subheader("Manage Uploaded Documents")
    docs = supabase.table("spiritual_knowledge").select("source").execute()

    if not docs.data:
        st.info("No documents found in the database.")
    else:
        sources = sorted(list(set([d["source"] for d in docs.data])))
        selected = st.selectbox("Select a document:", sources)

        if selected:
            # Count chunks
            count = supabase.table("spiritual_knowledge").select("id", count="exact").eq("source", selected).execute()
            st.markdown(f"**Chunks in '{selected}':** {count.count}")

            # Preview chunks
            rows = supabase.table("spiritual_knowledge").select("content").eq("source", selected).limit(3).execute()
            for i, r in enumerate(rows.data, 1):
                st.text_area(f"Chunk {i}", r["content"], height=100)

            # Delete button
            if st.button(f"❌ Delete '{selected}'"):
                supabase.table("spiritual_knowledge").delete().eq("source", selected).execute()
                st.success(f"'{selected}' deleted successfully.")
                st.rerun()
