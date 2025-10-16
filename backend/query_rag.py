import os
from openai import OpenAI
from supabase_utils import supabase
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context_from_supabase(query: str, match_count=5):
    # Step 1: create embedding for user query
    emb = client.embeddings.create(
        model="text-embedding-3-large",
        input=query
    ).data[0].embedding

    # Step 2: retrieve top matches from Supabase
    res = supabase.rpc(
        "match_documents",
        {"query_embedding": emb, "match_count": match_count}
    ).execute()

    if not res.data:
        return ""

    # Step 3: join top text chunks into one context block
    return "\n\n".join([r["content"] for r in res.data])

def generate_answer(query: str):
    # Get context text from Supabase
    context = get_context_from_supabase(query)

    system_prompt = (
        "You are Wellie, a calm and wise spiritual wellness coach. "
        "Use the provided context to answer the question accurately and kindly. "
        "If the context lacks enough detail, reply politely based on your general knowledge."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]

    # Step 4: send to OpenAI chat model
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.6
    )

    return result.choices[0].message.content
