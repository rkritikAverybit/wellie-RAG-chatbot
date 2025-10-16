# backend/test_insert.py
import os
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

text = "Meditation helps calm the mind and improve focus."
emb = client.embeddings.create(model="text-embedding-3-large", input=text).data[0].embedding

supabase.table("spiritual_knowledge").insert({
    "source": "test_doc",
    "section": "part_1",
    "content": text,
    "embedding": emb,
}).execute()

print("✅ test row inserted")
