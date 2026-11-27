import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import User
from models.schemas import (
    RefreshTokenRequest,
    Token,
    UserSignup,
    UserSignupResponse,
)
from utils.dependencies import get_current_user, oauth2_scheme, require_role
from utils.notifications import send_welcome_notification
from utils.rate_limiter import check_login_rate_limit
from utils.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from utils.token_blocklist import block_token

router = APIRouter()


# Admin dashboard view
@router.get("/admin")
def admin_dashboard(current_user: User = Depends(require_role("admin"))):
    return {
        "message": "Welcome to Admin Dashboard",
        "user": current_user.name,
        "role": current_user.role,
    }


# User Signup
@router.post(
    "/signup",
    response_model=UserSignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    user_data: UserSignup,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password_hash=hashed_password,
        role="claimant",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Schedule welcome notification after successful signup.
    # background_tasks.add_task(
    #     send_welcome_notification,
    #     new_user.email,
    #     new_user.name,
    # )

    # Send welcome notification through celery
    send_welcome_notification.delay(
        new_user.email,
        new_user.name,
    )

    return new_user


# User Login
@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    # Apply rate limiting based on client IP
    client_ip = request.client.host if request.client else "unknown"

    try:
        allowed, retry_after = check_login_rate_limit(client_ip)

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login service temporarily unavailable",
        )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(User).filter(User.email == form_data.username).first()

    if (
        not user
        or not user.password_hash
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": str(user.user_id),
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store only the refresh token hash
    user.refresh_token_hash = hash_refresh_token(refresh_token)

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Refresh Access Token
@router.post("/refresh", response_model=Token)
def refresh_access_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        token_data = decode_access_token(payload.refresh_token)

        if token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = int(token_data.get("sub"))

    except (InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user or not user.refresh_token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is no longer valid",
        )

    # Verify refresh token against stored hash
    if user.refresh_token_hash != hash_refresh_token(payload.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is no longer valid",
        )

    token_data = {
        "sub": str(user.user_id),
        "role": user.role,
    }

    # Generate new tokens
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Rotate stored refresh token hash
    user.refresh_token_hash = hash_refresh_token(new_refresh_token)

    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


# User Logout
@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Decode the current access token
    payload = decode_access_token(token)

    jti = payload["jti"]
    expiration = payload["exp"]

    # Calculate remaining token lifetime
    ttl = int(expiration - time.time())

    try:
        # Blocklist the access token in Redis
        if ttl > 0:
            block_token(jti, ttl)

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not complete logout. Try again later.",
        )

    # Invalidate the refresh token
    current_user.refresh_token_hash = None

    db.commit()

    return {"message": "Successfully logged out"}


# Get Logged-in User
@router.get("/me", response_model=UserSignupResponse)
def get_logged_in_user(current_user: User = Depends(get_current_user)):
    return current_user
