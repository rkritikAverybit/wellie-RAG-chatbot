from fastapi import FastAPI, Request, HTTPException
from query_rag import generate_answer

app = FastAPI(title="Wellie Chatbot RAG API")

@app.get("/health")
def health():
    return {"status": "ok", "message": "Chatbot API is running"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field")

    try:
        answer = generate_answer(prompt)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail={f"RAG error: {e}"})


from query_rag import get_context_from_supabase

@app.post("/debug")
async def debug(request: Request):
    data = await request.json()
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field")

    try:
        context = get_context_from_supabase(prompt)
        return {"retrieved_context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {e}")
