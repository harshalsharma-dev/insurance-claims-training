import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# Add a token to the blocklist
def block_token(jti: str, ttl: int):
    redis_client.setex(name=f"blocklist:{jti}", time=ttl, value="revoked")


# Check whether a token is blocklisted
def is_token_blocklisted(jti: str) -> bool:
    return redis_client.exists(f"blocklist:{jti}") == 1
