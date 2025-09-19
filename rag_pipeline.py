import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from google.generativeai import GenerativeModel, configure
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY in .env file")
configure(api_key=api_key)
gemini_model = GenerativeModel('gemini-2.5-flash')


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


MODEL_DIR = "/app/model_cache"  
os.makedirs(MODEL_DIR, exist_ok=True)

embedding_model_name = "nlpaueb/legal-bert-base-uncased"


embedding_tokenizer = AutoTokenizer.from_pretrained(
    embedding_model_name,
    cache_dir=MODEL_DIR
)
embedding_model = AutoModel.from_pretrained(
    embedding_model_name,
    cache_dir=MODEL_DIR
)

VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 768))


def embed_query(query: str) -> list[float]:
    """Generate embedding for a query using Legal-BERT"""
    inputs = embedding_tokenizer(
        query,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )
    with torch.no_grad():
        outputs = embedding_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy().tolist()


def retrieve_relevant_chunks(query: str, top_k: int = 5):
    """Retrieve relevant documents from Supabase using the query embedding."""
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
