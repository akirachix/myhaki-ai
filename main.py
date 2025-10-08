import os
from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import run_rag, get_embedding_model

app = FastAPI(title="MyHaki Agent")

class CaseInput(BaseModel):
    case_description: str
    trial_date: str  

@app.on_event("startup")
def preload_model():
    get_embedding_model()
    print("Embedding model loaded successfully.")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "FastAPI running on Cloud Run"}

@app.post("/predict/")
def predict_case(data: CaseInput):
    query = f"Case: {data.case_description}"
    results = run_rag(query, trial_date=data.trial_date)
    return {
        "input": {
            "case_description": data.case_description,
            "trial_date": data.trial_date
        },
        "prediction": results
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

