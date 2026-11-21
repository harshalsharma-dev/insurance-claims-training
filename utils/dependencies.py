from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt import InvalidTokenError
from redis.exceptions import RedisError


from database import get_db
from models.db_models import User
from utils.security import decode_access_token
from utils.token_blocklist import is_token_blocklisted

# Extract Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Get currently authenticated user
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = int(payload.get("sub"))
        jti = payload.get("jti")

        if not jti:
            raise credentials_exception

    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    # Check Redis blocklist
    try:
        if is_token_blocklisted(jti):
            raise credentials_exception

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )

    current_user = db.query(User).filter(User.user_id == user_id).first()

    if not current_user:
        raise credentials_exception

    return current_user


def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker
