from fastapi import APIRouter, HTTPException, Header, Response, Cookie, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from database import get_db

from models.db_models import Claim, Policy
from models.schemas import ClaimCreate, ClaimOut, ClaimUpdate, ClaimPatch

router = APIRouter()


@router.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    return {"message": "Database session received successfully"}


@router.get("/search", response_model=List[ClaimOut])
def search_claims_by_type(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Claim)

    if q:
        query = query.filter(Claim.claim_type.ilike(q))

    return query.all()


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim_details(
    claim_id: int,
    db: Session = Depends(get_db),
):
    # Step 1: Find claim by ID
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()

    # Step 2: Check whether claim exists
    if not claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    # Step 3: Return claim
    return claim


@router.put("/{claim_id}", response_model=ClaimOut)
def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    db: Session = Depends(get_db),
):
    # Step 1: Find existing claim
    existing_claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()

    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    # Step 2: Find the policy provided in request
    policy = (
        db.query(Policy).filter(Policy.policy_number == payload.policy_number).first()
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"Policy {payload.policy_number} not found",
        )

    # Step 3: Update existing claim fields
    existing_claim.policy_id = policy.policy_id
    existing_claim.claim_type = payload.claim_type
    existing_claim.claim_amount = payload.claim_amount
    existing_claim.status = payload.status
    existing_claim.description = payload.description
    existing_claim.priority = payload.priority

    # Step 4: Save changes
    db.commit()

    # Step 5: Refresh updated object
    db.refresh(existing_claim)

    return existing_claim


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


@router.get("", response_model=List[ClaimOut])
def get_claims(db: Session = Depends(get_db)):

    claims = db.query(Claim).all()

    return claims


@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
):
    # Step 1: Find policy using policy number
    policy = (
        db.query(Policy).filter(Policy.policy_number == payload.policy_number).first()
    )

    # Step 2: Check whether policy exists
    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"Policy {payload.policy_number} not found",
        )

    # Step 3: Create SQLAlchemy Claim object
    new_claim = Claim(
        policy_id=policy.policy_id,
        claim_type=payload.claim_type,
        claim_amount=payload.claim_amount,
        description=payload.description,
        priority=payload.priority,
    )

    # Step 4: Add object to database session
    db.add(new_claim)

    # Step 5: Commit transaction
    db.commit()

    # Step 6: Refresh object with database-generated values
    db.refresh(new_claim)

    # Step 7: Return created claim
    return new_claim


@router.patch("/{claim_id}", response_model=ClaimOut)
def patch_claim(
    claim_id: int,
    payload: ClaimPatch,
    db: Session = Depends(get_db),
):
    # Step 1: Find existing claim
    existing_claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()

    # Step 2: Handle claim not found
    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    # Step 3: Extract only fields provided by client
    update_data = payload.model_dump(exclude_unset=True)

    # Step 4: Apply updates to existing ORM object
    for field, value in update_data.items():
        setattr(existing_claim, field, value)

    # Step 5: Save changes
    db.commit()

    # Step 6: Refresh updated object
    db.refresh(existing_claim)

    return existing_claim


@router.delete("/{claim_id}", status_code=204)
def delete_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    # Step 1: Find existing claim
    existing_claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()

    # Step 2: Handle claim not found
    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    # Step 3: Delete claim
    db.delete(existing_claim)

    # Step 4: Commit deletion
    db.commit()

    return Response(status_code=204)
