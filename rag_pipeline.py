import json
import functools
import os
from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel, configure
from datetime import datetime
from supabase import create_client
from google.api_core import exceptions


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY in .env file")
configure(api_key=api_key)
gemini_model = GenerativeModel('gemini-2.5-flash')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 768))

@functools.lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

def embed_query(query: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(query).tolist()

def retrieve_relevant_chunks(query: str, top_k: int = 5):
    query_embedding = embed_query(query)
    response = supabase.rpc(
        "match_legal_embeddings",
        {"query_embedding": query_embedding, "match_count": top_k}
    ).execute()
    docs = [row["document"] for row in response.data] if response.data else []
    metas = [row["metadata"] for row in response.data] if response.data else []
    return docs, metas

def determine_urgency_from_date(trial_date_str: str) -> str:
    today = datetime.today().date()
    trial_date = datetime.strptime(trial_date_str, "%Y-%m-%d").date()
    days_until_trial = (trial_date - today).days
    if days_until_trial <= 15:
        return "urgent"
    elif days_until_trial <= 30:
        return "high"
    else:
        return "normal"

def generate_response(query: str, retrieved_docs: list[str], metadatas: list[dict], gemini_model, trial_date: str = None) -> dict:
    context = "\n".join([doc for doc in retrieved_docs if doc])
    metadata_context = "\n".join([f"Metadata {i+1}: {json.dumps(meta)}" for i, meta in enumerate(metadatas)])

    prompt = f"""
You are a legal assistant AI.
Analyze the following context and query, then return ONLY the following fields in JSON format:
- case_type: inferred case type(s)
- urgency: classify as "urgent" or "normal"
- reasoning: a short explanation of why you classified it this way

Context:
{context}

Metadata:
{metadata_context}

Query:
{query}

Respond strictly in JSON with keys: case_type, urgency, reasoning. Do not include anything else.
"""

    response = gemini_model.generate_content(prompt)
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "case_type": None,
            "urgency": None,
            "reasoning": raw_text
        }

    if trial_date:
        result["urgency"] = determine_urgency_from_date(trial_date)

    return result

def run_rag(query: str, trial_date: str = None):
    retrieved_docs, metadatas = retrieve_relevant_chunks(query)
    answer = generate_response(query, retrieved_docs, metadatas, gemini_model, trial_date=trial_date)
    return {
        "query": query,
        "response": answer
    }
