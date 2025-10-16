import os
from io import BytesIO
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document
import tiktoken

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
enc = tiktoken.get_encoding("cl100k_base")

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
        chunk = tokens[i:i+chunk_size]
        chunks.append(enc.decode(chunk))
        i += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]

def upload_to_supabase(source, text, lang="en"):
    chunks = chunk_text(text)
    st_count = len(chunks)
    print(f"Creating {st_count} embeddings...")

    embeddings = client.embeddings.create(model="text-embedding-3-large", input=chunks)
    vectors = [e.embedding for e in embeddings.data]

    rows = []
    for i, (c, v) in enumerate(zip(chunks, vectors)):
        rows.append({
            "source": source,
            "section": f"{source}_part_{i+1}",
            "content": c,
            "embedding": v,
            "metadata": {"lang": lang},
        })

    batch_size = 100
    for i in range(0, len(rows), batch_size):
        supabase.table("spiritual_knowledge").upsert(rows[i:i+batch_size]).execute()

    return st_count
