from fastapi import APIRouter, HTTPException, Header, Response, Cookie, Depends
from typing import Optional, List
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Claim, Policy, User
from models.schemas import ClaimCreate, ClaimOut, ClaimUpdate, ClaimPatch
from utils.dependencies import get_current_user

router = APIRouter()


# Admins can access all claims.
# Claimants can access only their own claims.
def get_claims_query(db: Session, current_user: User):
    query = db.query(Claim)

    if current_user.role != "admin":
        query = query.filter(Claim.user_id == current_user.user_id)

    return query


# Associate a policy with a user if not already associated.
def associate_policy_with_user(
    db: Session,
    user: User,
    policy: Policy,
):
    existing_association = (
        db.query(Claim.__table__.metadata.tables["user_policies"])
        .filter_by(
            user_id=user.user_id,
            policy_id=policy.policy_id,
        )
        .first()
    )

    if not existing_association:
        user.policies.append(policy)


# Test database connection
@router.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    return {"message": "Database session received successfully"}


# Cookie testing route
@router.get("/cookie")
def set_delete_cookies(
    response: Response,
    user_agent: str = Header(default=None),
    session_id: str = Cookie(default=None),
):
    response.headers["X-System-Name"] = "Insurance-Claims-API"

    response.set_cookie(
        key="session_id",
        value="session123",
        httponly=True,
        secure=True,
        samesite="lax",
    )

    if session_id:
        response.delete_cookie(
            key="session_id",
            httponly=True,
            secure=True,
        )

    return {}


# Search claims
@router.get("/search", response_model=List[ClaimOut])
def search_claims_by_type(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = get_claims_query(db, current_user)

    if q:
        query = query.filter(Claim.claim_type.ilike(f"%{q}%"))

    return query.all()


# Get all claims
@router.get("", response_model=List[ClaimOut])
def get_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_claims_query(db, current_user).all()


# Create claim
@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find one of the three predefined policies.
    policy = (
        db.query(Policy).filter(Policy.policy_number == payload.policy_number).first()
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        )

    # Associate this policy with the logged-in user.
    associate_policy_with_user(db, current_user, policy)

    # Claim type is determined automatically from the policy.
    new_claim = Claim(
        user_id=current_user.user_id,
        policy_id=policy.policy_id,
        claim_type=policy.policy_type,
        claim_amount=payload.claim_amount,
        description=payload.description,
        priority=payload.priority,
    )

    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)

    return new_claim


# Update complete claim
@router.put("/{claim_id}", response_model=ClaimOut)
def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_claim = (
        get_claims_query(db, current_user).filter(Claim.claim_id == claim_id).first()
    )

    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    # Find the requested predefined policy.
    policy = (
        db.query(Policy).filter(Policy.policy_number == payload.policy_number).first()
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found",
        )

    # Associate the policy with the actual claim owner.
    claim_owner = existing_claim.user
    associate_policy_with_user(db, claim_owner, policy)

    existing_claim.policy_id = policy.policy_id
    existing_claim.claim_type = policy.policy_type
    existing_claim.claim_amount = payload.claim_amount
    existing_claim.status = payload.status
    existing_claim.description = payload.description
    existing_claim.priority = payload.priority

    db.commit()
    db.refresh(existing_claim)

    return existing_claim


# Partially update claim
@router.patch("/{claim_id}", response_model=ClaimOut)
def patch_claim(
    claim_id: int,
    payload: ClaimPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_claim = (
        get_claims_query(db, current_user).filter(Claim.claim_id == claim_id).first()
    )

    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(existing_claim, field, value)

    db.commit()
    db.refresh(existing_claim)

    return existing_claim


# Delete claim
@router.delete("/{claim_id}", status_code=204)
def delete_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_claim = (
        get_claims_query(db, current_user).filter(Claim.claim_id == claim_id).first()
    )

    if not existing_claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    db.delete(existing_claim)
    db.commit()

    return Response(status_code=204)


# Get claim by ID
@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim_details(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    claim = (
        get_claims_query(db, current_user).filter(Claim.claim_id == claim_id).first()
    )

    if not claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim with ID {claim_id} not found",
        )

    return claim
