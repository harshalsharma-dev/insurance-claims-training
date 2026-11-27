import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm


# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Password verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT access token generation
def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# JWT refresh token generation
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# JWT access token verification
def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# Hash refresh token before storing in database
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
