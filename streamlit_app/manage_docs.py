import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

st.set_page_config(page_title="Manage Documents", page_icon="🗂")
st.title("🗂 Manage Uploaded Documents")

# Fetch all distinct sources
data = supabase.table("spiritual_knowledge").select("source").execute()
if not data.data:
    st.info("No documents uploaded yet.")
    st.stop()

sources = sorted(list(set([d["source"] for d in data.data])))
selected = st.selectbox("Select a document to view or delete:", sources)

# Count chunks for this source
count = supabase.table("spiritual_knowledge").select("id", count="exact").eq("source", selected).execute()
st.markdown(f"**Chunks for '{selected}':** {count.count}")

# Show preview of first few chunks
rows = supabase.table("spiritual_knowledge").select("content").eq("source", selected).limit(3).execute()
for i, r in enumerate(rows.data, 1):
    st.text_area(f"Chunk {i}", r["content"], height=120)

# Delete button
if st.button(f"❌ Delete '{selected}' from database"):
    supabase.table("spiritual_knowledge").delete().eq("source", selected).execute()
    st.success(f"'{selected}' deleted successfully.")
    st.rerun()
