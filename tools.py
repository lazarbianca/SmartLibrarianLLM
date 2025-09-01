# tools.py
import json, re
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from pathlib import Path


load_dotenv(override=True)

# --- Core RAG constants ---
EMBED_MODEL = "text-embedding-3-small"
GIBBERISH_DISTANCE_THRESH = 0.75

# --- OpenAI + Chroma singletons ---
_client = OpenAI()
_chroma = chromadb.PersistentClient(path="chroma_db", settings=Settings(allow_reset=False))

def _get_or_create_collection(name: str = "books"):
    try:
        return _chroma.get_collection(name)
    except Exception:
        # cosine matches the index you created in rag_init.py
        return _chroma.create_collection(name=name, metadata={"hnsw:space": "cosine"})

# --- Embedding + retrieve ---
def embed_query(text: str):
    r = _client.embeddings.create(model=EMBED_MODEL, input=[text])
    return r.data[0].embedding

def retrieve(query: str, k: int = 6):
    coll = _get_or_create_collection("books")
    q_emb = embed_query(query)
    res = coll.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    if not res["ids"] or not res["ids"][0]:
        return [], 1.0

    ids = res["ids"][0]
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    cands = [{"title": ids[i], "short": docs[i], "full": metas[i]["full"]} for i in range(len(ids))]
    best_dist = res["distances"][0][0] if res.get("distances") and res["distances"][0] else 1.0
    return cands, best_dist

# --- Gibberish/bad-words helpers ---
def looks_like_gibberish(text: str) -> bool:
    s = (text or "").strip()
    if len(s) < 3:
        return True
    if re.fullmatch(r'[^A-Za-z\u00C0-\u024F]+', s):  # only non-letters
        return True
    letters = re.findall(r'[A-Za-z\u00C0-\u024F]', s)
    if len(letters) / max(1, len(s)) < 0.5:          # too many non-letters
        return True
    if re.search(r'(?i)[bcdfghjklmnpqrstvwxz]{6,}', s):  # absurd consonant cluster
        return True
    if re.search(r'(.)\1{4,}', s):  # xxxxx
        return True
    if not re.findall(r'[A-Za-z\u00C0-\u024F]{2,}', s):  # no word-like tokens
        return True
    return False

BAD_WORDS = {"idiot", "stupid", "fuck", "shit"}  # expand as needed

def is_inappropriate(text: str) -> bool:
    lower = (text or "").lower()
    return any(w in lower for w in BAD_WORDS)


DATA_FILE = (Path(__file__).parent / "data" / "book_summaries.json").resolve()

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        _BOOKS = {b["title"]: b for b in json.load(f)}
except Exception as e:
    _BOOKS = {}
    # Optional: print(f"[tools] WARNING: couldn't load {DATA_FILE}: {e}")

def get_summary_by_title(title: str) -> str:
    """Returns the full summary for an exact title."""
    book = _BOOKS.get(title)
    if not book:
        return f"I couldn't find a summary for \"{title}\"."
    return book["full"]