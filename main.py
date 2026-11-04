from fastapi import FastAPI
from sample_records import claims
from typing import Optional

app = FastAPI(
    title="Insurance Claims",
    description="API for managing Motor, Health and Property Insurance Claims",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


@app.get("/claims")
def get_claims():
    return claims


@app.get("/search")
def search_claims(q: Optional[str] = None):

    if q is None:
        return claims

    filtered_claims = []

    for val in claims:
        if val["claim_type"].lower() == q.lower():
            filtered_claims.append(val)

    if filtered_claims:
        return filtered_claims
    else:
        return {"message": f"No claims found for claim type: '{q}'"}


@app.get("/claims/{claim_id}")
def get_claim(claim_id: int):

    for claim in claims:
        if claim["claim_id"] == claim_id:
            return claim

    return {"message": "Claim not found"}
