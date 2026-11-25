import json

from utils.token_blocklist import redis_client

# Cache duration: 60 seconds
CACHE_TTL = 60


# Generate a unique cache key for each user and pagination request
def get_claims_cache_key(
    user_id: int,
    role: str,
    skip: int,
    limit: int,
) -> str:
    return f"claims_cache:{user_id}:{role}:{skip}:{limit}"


# Retrieve cached claims
def get_cached_claims(cache_key: str):
    cached_data = redis_client.get(cache_key)

    if cached_data is None:
        return None

    return json.loads(cached_data)


# Store claims in Redis
def set_cached_claims(cache_key: str, claims: list):
    redis_client.setex(
        name=cache_key,
        time=CACHE_TTL,
        value=json.dumps(claims),
    )


# Invalidate all cached claims lists
def invalidate_claims_cache():
    cache_keys = list(redis_client.scan_iter(match="claims_cache:*"))

    if cache_keys:
        redis_client.delete(*cache_keys)
