import json, os
import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from openai import OpenAI

load_dotenv(override=True)  # ensures .env always wins

client = OpenAI()

CHROMA_DIR = "chroma_db"

def embed(texts):
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [d.embedding for d in resp.data]

def main():
    # init chroma (local persistent)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=True))
    try:
        chroma_client.delete_collection("books")
    except:
        pass
    coll = chroma_client.create_collection(name="books", metadata={"hnsw:space": "cosine"})

    # load data
    with open("data/book_summaries.json", "r", encoding="utf-8") as f:
        books = json.load(f)

    # use the 'short' field (themes) as retrievable content
    texts = [b["short"] for b in books]
    ids = [b["title"] for b in books]
    metadatas = [{"title": b["title"], "full": b["full"]} for b in books]

    embs = embed(texts)
    coll.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=embs)
    print(f"Indexed {len(books)} books into Chroma at {CHROMA_DIR}")

if __name__ == "__main__":
    main()
