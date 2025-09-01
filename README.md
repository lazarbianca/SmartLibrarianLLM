# Smart Librarian — RAG Book Recommender

FastAPI backend + MUI (Vite React) frontend that recommends **exactly one book** based on your themes/mood.
Uses **OpenAI embeddings** + **Chroma** for retrieval (RAG) and adds guardrails for gibberish/inappropriate input.

## Features
- 🔎 **RAG** over local `data/book_summaries.json` (themes + full summaries)
- 🧮 **Chroma** persistent vector DB (`chroma_db/`)
- 🧠 **OpenAI**: `text-embedding-3-small` for retrieval; `gpt-4o-mini` for reasoning
- 🛡️ Guardrails: gibberish check, distance threshold, LLM “ABSTAIN” fallback
- 🧑‍💻 CLI (optional) and **MUI** web UI

## Tech Stack
- Backend: Python 3.10+ · FastAPI · ChromaDB · OpenAI · python-dotenv
- Frontend: Vite + React + TypeScript · Material UI · (Framer Motion optional)

## Repository Structure
```
.
├─ api.py                 # FastAPI app (run with: python api.py)
├─ tools.py               # shared RAG helpers & guardrails (core logic)
├─ rag_init.py            # one-time (re)indexing into Chroma
├─ chat_cli.py            # optional CLI for quick testing
├─ data/
│  └─ book_summaries.json # your dataset (≥10 entries)
├─ chroma_db/             # local vector DB (ignored by git)
└─ smart-librarian-ui/    # Vite + React + MUI frontend
```

---

## Setup

### 0) Environment variables
Create **`.env`** in the repo root (do **not** commit this file):
```
OPENAI_API_KEY=sk-...
```

### 1) Python dependencies

**Windows PowerShell**
```powershell
# (optional) create venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# install deps
pip install fastapi "uvicorn[standard]" chromadb python-dotenv openai
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" chromadb python-dotenv openai
```

### 2) Build (or rebuild) the vector index
Run this **whenever** you change `data/book_summaries.json`, the embedding model, or delete `chroma_db/`.

```bash
python rag_init.py
```
This reads `data/book_summaries.json`, embeds each book’s `short` themes, and writes vectors to `chroma_db/`.

### 3) Run the API (without uvicorn CLI)
```bash
python api.py
```
This starts FastAPI on **http://127.0.0.1:8000**.

Health check:
```bash
curl http://127.0.0.1:8000/health
```

### 4) Run the frontend (Vite + MUI)
```bash
cd smart-librarian-ui
npm install
npm run dev
```
Open **http://localhost:5173**.  
The frontend calls the backend at `http://localhost:8000/chat`.

---

## API

### `POST /chat`
**Body**
```json
{ "query": "give me a book about magic" }
```

**Response (200)**
```json
{
  "title": "The Name of the Wind",
  "reason": "Selected based on theme similarity to your request: \"give me a book about magic\".",
  "summary": "..."
}
```

**Possible 400 errors**
- `Empty question.`
- `Please keep it polite and safe.`
- `I couldn't understand that. Try a clearer request (e.g., 'dark fantasy about loyalty').`
- `No close matches. Add topics, mood, or genre.`

### `GET /health`
```json
{ "ok": true }
```

---

## How it works (short)
1. **Indexing** (`rag_init.py`): each book’s `short` themes are embedded with OpenAI and stored in Chroma with metadata (title + full summary).
2. **Query** (`/chat`): the user query is embedded; Chroma returns the **nearest** books.
3. **Pick**: the LLM chooses **one** title from those candidates (or **ABSTAIN** on nonsense).
4. **Answer**: the API fetches the full summary for that title and returns a friendly response.

### Guardrails
- `looks_like_gibberish`: filters out keysmashes / non-language input.
- Distance threshold (`GIBBERISH_DISTANCE_THRESH` in `tools.py`): blocks only if the query is extremely short **and** the best match is far.
- LLM prompt with **ABSTAIN** token to avoid forced recommendations.

---

## Git: ignore secrets & push

Add this `.gitignore` at repo root:

```gitignore
# --- Python / FastAPI ---
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.log
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.venv/
venv/
env/
ENV/

# Local env files (keep example only)
.env
.env.*
!.env.example

# Chroma (local vector DB)
chroma_db/

# --- Node / Vite frontend ---
smart-librarian-ui/node_modules/
smart-librarian-ui/dist/
smart-librarian-ui/.vite/
smart-librarian-ui/.cache/
smart-librarian-ui/npm-debug.log*
smart-librarian-ui/yarn-error.log*
smart-librarian-ui/pnpm-debug.log*
smart-librarian-ui/.env
smart-librarian-ui/.env.*
!smart-librarian-ui/.env.example

# --- Editors / OS ---
.vscode/
.idea/
*.code-workspace
.DS_Store
Thumbs.db
```

Create a minimal `.env.example`:
```
OPENAI_API_KEY=your-key-here
```

First-time GitHub push (with GitHub CLI):
```bash
git init
git add -A
git commit -m "Initial commit: Smart Librarian RAG (API + MUI frontend)"
git branch -M main
gh repo create smart-librarian-llm --private --source=. --remote=origin --push
```

Without `gh`:
```bash
git init
git add -A
git commit -m "Initial commit: Smart Librarian RAG (API + MUI frontend)"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<REPO-NAME>.git
git push -u origin main
```

Double-check `.env` won’t be pushed:
```bash
git check-ignore -v .env smart-librarian-ui/.env
git ls-files .env smart-librarian-ui/.env   # should print nothing
```

---

## Troubleshooting
- **“Failed to fetch”** in the browser: ensure API is running at `http://127.0.0.1:8000` and CORS allows `http://localhost:5173`.
- **500 on `/chat`**: check API logs; common cause is import errors or missing data path. Use absolute path in `tools.py` for `book_summaries.json`.
- **Too many “No close matches”**: increase `GIBBERISH_DISTANCE_THRESH` in `tools.py` (try `0.70–0.80`) and/or add more descriptive themes.
- **Block nonsense (`AJDFKJ...`)**: covered by gibberish heuristic, short+far distance gate, and ABSTAIN prompt.

## License
MIT (or your choice)
