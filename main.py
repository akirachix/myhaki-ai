from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import run_rag

app = FastAPI()

class CaseInput(BaseModel):
    case_description: str
    trial_date: str  

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
