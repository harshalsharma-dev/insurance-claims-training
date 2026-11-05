from fastapi import FastAPI
from sample_records import claims
from typing import Optional, List
from pydantic import BaseModel, Field


class PolicyholderDetails(BaseModel):
    name: str
    email: str
    phone_number: int


class Claim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_type: str
    claim_amount: float = Field(gt=0, lt=100000)
    policyholder: PolicyholderDetails
    description: Optional[str] = None


class CreateClaimDetailResponse(BaseModel):
    policy_number: str
    claim_type: str
    claim_amount: float


class CreateClaimResponse(BaseModel):
    message: str
    claim: CreateClaimDetailResponse


class ClaimsResponse(BaseModel):
    claim_id: int
    policy_number: str
    claim_type: str
    claim_amount: float
    status: str


app = FastAPI(
    title="Insurance Claims",
    description="API for managing Motor, HealthClaim and Property Insurance Claims",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


@app.get("/claims", response_model=List[ClaimsResponse])
def get_claims():
    return claims


@app.get("/search")
def search_claims_by_type(q: Optional[str] = None):

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


@app.post("/create-claim", response_model=CreateClaimResponse)
def create_claim(claim: Claim):

    return {
        "message": "Insurance claim submitted successfully",
        "claim": claim,
    }
