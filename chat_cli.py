# chat_cli.py
from dotenv import load_dotenv
from openai import OpenAI
import json

from tools import (
    retrieve,
    looks_like_gibberish,
    is_inappropriate,
    get_summary_by_title,
    GIBBERISH_DISTANCE_THRESH,
)

load_dotenv(override=True)
client = OpenAI()

SYSTEM = (
    "You are Smart Librarian. Recommend exactly one book per user query. "
    "First, use retrieved context to choose the best title. "
    "Then call the tool get_summary_by_title with that exact title. "
    "After tool output, reply in English with: "
    "1) Recommendation (Title + why it fits) 2) Detailed summary (from tool)."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_summary_by_title",
            "description": "Returns the full summary for an exact book title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The exact title of the book.",
                    }
                },
                "required": ["title"],
            },
        },
    }
]

ABSTAIN_TOKEN = "ABSTAIN"

def choose_title_from_context(user_query, retrieved, best_distance, threshold):
    titles_list = ", ".join(b["title"] for b in retrieved)
    msg = [
        {
            "role": "system",
            "content": (
                "You are a strict title selector. Only choose from the list. "
                f"If BestDistance > {threshold} or the request is gibberish / not about books, "
                f"reply EXACTLY with '{ABSTAIN_TOKEN}'. Never invent a title."
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
    r = client.chat.completions.create(model="gpt-4o-mini", messages=msg, temperature=0)
    return r.choices[0].message.content.strip()

def run_cli():
    print("Smart Librarian (type 'quit' to exit)")
    while True:
        user = input("\nYou: ").strip()
        if user.lower() in {"quit", "exit"}:
            break

        if is_inappropriate(user):
            print("Librarian: Let's keep it polite. Please rephrase.")
            continue
        if looks_like_gibberish(user):
            print("Librarian: I couldn't understand that. Try a clearer request (e.g., 'dark fantasy about loyalty').")
            continue

        # RAG retrieve
        cands, best_dist = retrieve(user, k=6)
        title_or_abstain = choose_title_from_context(user, cands, best_dist, GIBBERISH_DISTANCE_THRESH)
        if title_or_abstain.upper() == ABSTAIN_TOKEN:
            print("Librarian: I couldn't match that to any themes. Try adding topics, mood, or genre.")
            continue

        chosen_title = title_or_abstain
        # Ask the model to call the tool
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "system", "content": f"RAG context (candidates): {', '.join(b['title'] for b in cands)}"},
            {"role": "user", "content": f"Use the title: {chosen_title}. Call the tool, then write the answer."},
        ]
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "get_summary_by_title"}},
        )

        msg = resp.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            if tc.function.name == "get_summary_by_title":
                args = json.loads(tc.function.arguments)
                summary = get_summary_by_title(args["title"])

                follow = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                    + [
                        {"role": "assistant", "tool_calls": msg.tool_calls},
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": "get_summary_by_title",
                            "content": summary,
                        },
                    ],
                    temperature=0.4,
                )
                print(f"\nLibrarian:\n{follow.choices[0].message.content}")
        else:
            # fallback
            print(f"\nLibrarian:\n{msg.content}")

if __name__ == "__main__":
    run_cli()
