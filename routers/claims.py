import time
import asyncio
from fastapi import (
    APIRouter,
    HTTPException,
    Header,
    Response,
    Cookie,
    Depends,
    BackgroundTasks,
    Request,
)
from typing import Optional, List
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Claim, Policy, User
from models.schemas import ClaimCreate, ClaimOut, ClaimUpdate, ClaimPatch
from utils.dependencies import get_current_user
from utils.dependencies import (
    verify_api_key,
    APIKeyChecker,
    pagination_params,
)
from utils.notifications import send_claim_notification

from redis.exceptions import RedisError

from utils.cache import (
    get_claims_cache_key,
    get_cached_claims,
    set_cached_claims,
    invalidate_claims_cache,
)
from utils.rate_limiter import check_token_bucket

router = APIRouter()
verify_api_key_class = APIKeyChecker("insurance-training-key")


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


# Invalidate cached claims safely
def clear_claims_cache():
    try:
        invalidate_claims_cache()
    except RedisError:
        # Database operation has already succeeded.
        # Remaining cache entries will expire through TTL.
        pass


# Test database connection with API key dependency
@router.get(
    "/test-db",
    dependencies=[Depends(verify_api_key_class)],
)
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
    request: Request,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(pagination_params),
):
    client_ip = request.client.host if request.client else "unknown"

    try:
        allowed, remaining_tokens, retry_after = check_token_bucket(client_ip)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Rate limiting service temporarily unavailable",
        )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many search requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    query = get_claims_query(db, current_user)

    if q:
        query = query.filter(Claim.claim_type.ilike(f"%{q}%"))

    return (
        query.order_by(Claim.claim_id)
        .offset(pagination["skip"])
        .limit(pagination["limit"])
        .all()
    )


# Get all claims with Redis caching
@router.get("", response_model=List[ClaimOut])
def get_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(pagination_params),
):
    # Generate a unique cache key
    cache_key = get_claims_cache_key(
        user_id=current_user.user_id,
        role=current_user.role,
        skip=pagination["skip"],
        limit=pagination["limit"],
    )

    # Try retrieving claims from Redis
    try:
        cached_claims = get_cached_claims(cache_key)

        if cached_claims is not None:
            return cached_claims

    except RedisError:
        # If Redis is unavailable, continue with PostgreSQL
        pass

    # Cache miss: fetch claims from PostgreSQL
    claims = (
        get_claims_query(db, current_user)
        .order_by(Claim.claim_id)
        .offset(pagination["skip"])
        .limit(pagination["limit"])
        .all()
    )

    # Convert SQLAlchemy objects into JSON-compatible dictionaries
    claims_data = [
        ClaimOut.model_validate(claim).model_dump(mode="json") for claim in claims
    ]

    # Store the result in Redis
    try:
        set_cached_claims(cache_key, claims_data)

    except RedisError:
        # Database response is still available
        pass

    return claims_data


# Create claim
@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreate,
    background_tasks: BackgroundTasks,
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

    clear_claims_cache()

    # Schedule notification after successful claim creation.
    background_tasks.add_task(
        send_claim_notification,
        current_user.email,
        new_claim.claim_id,
    )

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

    # Only admins can approve or reject claims
    if current_user.role != "admin" and payload.status != existing_claim.status:
        raise HTTPException(
            status_code=403,
            detail="Only admins can update claim status",
        )

    # Find the requested predefined policy
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

    clear_claims_cache()

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

    # Only admins can approve or reject claims
    if "status" in update_data and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can update claim status",
        )

    for field, value in update_data.items():
        setattr(existing_claim, field, value)

    db.commit()
    db.refresh(existing_claim)

    clear_claims_cache()

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

    clear_claims_cache()

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


@router.get("/test/blocking")
async def blocking_endpoint():
    print("BLOCKING: Request started")

    time.sleep(5)

    print("BLOCKING: Request completed")

    return {"message": "Blocking completed"}


@router.get("/test/non-blocking")
async def non_blocking_endpoint():
    print("NON-BLOCKING: Request started")

    await asyncio.sleep(5)

    print("NON-BLOCKING: Request completed")

    return {"message": "Non-blocking completed"}
