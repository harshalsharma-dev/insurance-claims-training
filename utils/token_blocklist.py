import redis

from config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def block_token(jti: str, ttl: int):
    redis_client.setex(
        name=f"blocklist:{jti}",
        time=ttl,
        value="revoked",
    )


def is_token_blocklisted(jti: str) -> bool:
    return redis_client.exists(f"blocklist:{jti}") == 1
