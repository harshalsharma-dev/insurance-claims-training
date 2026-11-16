from fastapi import APIRouter, HTTPException, Header, Response, Cookie, Depends
from typing import Optional, List, Literal
from models.schemas import ClaimsResponse, CreateClaimResponse, CreateClaim, UpdateClaim
from sample_records import claims
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    return {"message": "Database session received successfully"}


@router.get("", response_model=List[ClaimsResponse])
def get_claims():
    return claims


@router.get("/search")
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


@router.get("/{claim_id}")
def get_claim_details(claim_id: int):

    for claim in claims:
        if claim["claim_id"] == claim_id:
            return claim

    raise HTTPException(status_code=404, detail=f"Claim with ID {claim_id} not found")


@router.patch("/{claim_id}/status")
def update_claim_status(
    claim_id: int, payload: Literal["Pending", "Approved", "Rejected"]
):

    for claim in claims:
        if claim["claim_id"] == claim_id:
            claim["status"] = payload
            return claim

    raise HTTPException(
        status_code=404,
        detail=f"Claim with ID {claim_id} not found",
    )


@router.post("/create-claim", response_model=CreateClaimResponse, status_code=201)
def create_claim(claim: CreateClaim):

    next_id = max((item["claim_id"] for item in claims), default=100) + 1

    new_claim = {
        "claim_id": next_id,
        "status": "Pending",
        **claim.model_dump(),
    }

    claims.append(new_claim)

    return {
        "message": "Insurance claim submitted successfully",
        "claim": new_claim,
    }


@router.put("/{claim_id}")
def update_claim(claim_id: int, payload: UpdateClaim):
    for index, existing_claim in enumerate(claims):
        if existing_claim["claim_id"] == claim_id:
            # Build the replacement dictionary while keeping the original claim_id
            updated_claim = {
                "claim_id": claim_id,
                **payload.model_dump(),
            }
            # payload.model_dump() converts the validated Pydantic model (payload)—including the nested policyholder model—into a standard Python dictionary
            claims[index] = updated_claim
            return updated_claim

    raise HTTPException(
        status_code=404,
        detail=f"Claim with ID {claim_id} not found",
    )


@router.delete("/{claim_id}", status_code=204)
def delete_claim(claim_id: int):
    for index, val in enumerate(claims):
        if val["claim_id"] == claim_id:
            del claims[index]
            return
    raise HTTPException(status_code=404, detail=f"Claim with ID {claim_id} not found")


# this route is only for testing purpose
@router.get("/cookie")
def set_delete_cookies(
    response: Response,
    user_agent: str = Header(default=None),  # read the request headers
    session_id: str = Cookie(default=None),  # read cookies
):

    # set response headers
    response.headers["X-System-Name"] = "Insurance-Claims-API"

    # set cookies
    response.set_cookie(
        key="session_id", value="session123", httponly=True, secure=True, samesite="lax"
    )

    if session_id:
        response.delete_cookie(key="session_id", httponly=True, secure=True)

    return {}
