
from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import run_rag

app = FastAPI()


class CaseInput(BaseModel):
    case_description: str
    trial_date: str  

@app.post("/predict/")
def predict_case(data: CaseInput):
    query = f"Case: {data.case_description}. Trial Date: {data.trial_date}"
    results = run_rag(query)
    return {
        "input": {
            "case_description": data.case_description,
            "trial_date": data.trial_date
        },
        "response": results
    }
