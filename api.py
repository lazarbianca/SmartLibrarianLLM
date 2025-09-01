# api.py
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from openai import OpenAI

from tools import (
    retrieve,
    looks_like_gibberish,
    is_inappropriate,
    get_summary_by_title,
    GIBBERISH_DISTANCE_THRESH,
)

load_dotenv(override=True)
client = OpenAI()

ABSTAIN_TOKEN = "ABSTAIN"

def choose_title(user_query: str, candidates, best_distance: float, threshold: float):
    titles_list = ", ".join(b["title"] for b in candidates)
    messages = [
        {
            "role": "system",
            "content": (
            "You are a strict title selector. Choose exactly one title from the provided list. "
            "Reply EXACTLY with 'ABSTAIN' only if the request is not about books at all or is pure gibberish. "
            "Do NOT abstain solely because the BestDistance is moderately high; prefer the closest title. "
            "Never invent a title."
        ),

        },
        {
            "role": "user",
            "content": (
                f"Request: {user_query}\n"
                f"Candidates: {titles_list}\n"
                f"BestDistance: {best_distance}\n"
                f"Reply with ONE exact title from Candidates, or '{ABSTAIN_TOKEN}'."
            ),
        },
    ]
    r = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
    return r.choices[0].message.content.strip()

app = FastAPI()

# CORS for Vite dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatIn(BaseModel):
    query: str

class ChatOut(BaseModel):
    title: str
    reason: str
    summary: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    q = (body.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty question.")
    if is_inappropriate(q):
        raise HTTPException(status_code=400, detail="Please keep it polite and safe.")
    if looks_like_gibberish(q):
        raise HTTPException(status_code=400, detail="I couldn't understand that. Try a clearer request (e.g., 'dark fantasy about loyalty').")

    # Retrieve from Chroma
    cands, best_dist = retrieve(q, k=6)
    if not cands:
        raise HTTPException(status_code=400, detail="No candidates found.")

    # --- Soft gating ---
    # Only block if the query is extremely short AND the match is far.
    very_short = len(q) <= 3
    too_far = best_dist > GIBBERISH_DISTANCE_THRESH
    # Debug (optional): print distance to calibrate later
    print(f"[chat] best_dist={best_dist:.3f} very_short={very_short} too_far={too_far} q={q!r}")

    if very_short and too_far:
        raise HTTPException(status_code=400, detail="No close matches. Add topics, mood, or genre.")

    # Ask LLM to pick exactly one title, with ABSTAIN fallback
    title_or_abstain = choose_title(q, cands, best_dist, GIBBERISH_DISTANCE_THRESH)

    # If the model abstains but the query is not tiny, fall back to the top-1 candidate
    if title_or_abstain.upper() == ABSTAIN_TOKEN:
        if very_short:
            raise HTTPException(status_code=400, detail="No close matches. Add topics, mood, or genre.")
        title = cands[0]["title"]
    else:
        title = title_or_abstain

    reason = f"Selected based on theme similarity to your request: \"{q}\"."
    summary = get_summary_by_title(title)
    return ChatOut(title=title, reason=reason, summary=summary)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
