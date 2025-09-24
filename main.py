
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_pipeline import run_rag, get_embedding_model, get_gemini_model

app = FastAPI(
    title="Legal RAG API",
    description="An API for legal case analysis using RAG.",
    version="1.0.0"
)

class CaseInput(BaseModel):
    case_description: str
    trial_date: str

@app.post("/predict/", summary="Predict case type and urgency")
def predict_case(data: CaseInput):
    """Endpoint to predict case type and urgency based on description and trial date."""
    query = f"Case: {data.case_description}. Trial Date: {data.trial_date}"
    results = run_rag(query, trial_date=data.trial_date)
    return {
        "input": {
            "case_description": data.case_description,
            "trial_date": data.trial_date
        },
        "response": results
    }

@app.get("/warmup", summary="Pre-load models into memory")
def warmup_models():
    """
    Pre-loads all heavy models (Legal-BERT, Gemini) into memory.
    Call this endpoint after deployment to 'warm up' the service.
    Returns 200 if successful, 500 if an error occurs during loading.
    """
    try:
        tokenizer, model = get_embedding_model()
        gemini_model = get_gemini_model()
        return {"status": "success", "message": "Models pre-loaded and ready."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm up models: {str(e)}")

@app.get("/health", summary="Simple health check")
def health_check():
    """
    Simple health check that does NOT load models.
    Used by Cloud Run for liveness/readiness probes.
    """
    return {"status": "healthy", "message": "Service is running."}