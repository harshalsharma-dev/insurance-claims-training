import time

from utils.token_blocklist import redis_client

# Rate limit configuration
LOGIN_RATE_LIMIT = 5
LOGIN_WINDOW_SECONDS = 60


TOKEN_BUCKET_CAPACITY = 5
TOKEN_REFILL_RATE = 1 / 10  # 1 token every 10 seconds


# Check login request limit using Redis
def check_login_rate_limit(client_ip: str):
    key = f"login_attempts:{client_ip}"

    # Atomically increment counter and set expiry
    script = """
    local count = redis.call('INCR', KEYS[1])

    if count == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end

    local ttl = redis.call('TTL', KEYS[1])

    return {count, ttl}
    """

    count, ttl = redis_client.eval(
        script,
        1,
        key,
        LOGIN_WINDOW_SECONDS,
    )

    if count > LOGIN_RATE_LIMIT:
        return False, ttl

    return True, ttl


def check_token_bucket(client_ip: str):
    key = f"claims_search_bucket:{client_ip}"
    now = time.time()

    script = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local refill_rate = tonumber(ARGV[3])

    local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')

    local tokens = tonumber(bucket[1])
    local last_refill = tonumber(bucket[2])

    if tokens == nil then
        tokens = capacity
        last_refill = now
    end

    local elapsed = math.max(0, now - last_refill)
    tokens = math.min(capacity, tokens + elapsed * refill_rate)

    local allowed = 0

    if tokens >= 1 then
        tokens = tokens - 1
        allowed = 1
    end

    redis.call('HSET', key,
        'tokens', tokens,
        'last_refill', now
    )

    redis.call('EXPIRE', key, 3600)

    local retry_after = 0

    if allowed == 0 then
        retry_after = math.ceil((1 - tokens) / refill_rate)
    end

    return {allowed, tokens, retry_after}
    """

    allowed, remaining_tokens, retry_after = redis_client.eval(
        script,
        1,
        key,
        now,
        TOKEN_BUCKET_CAPACITY,
        TOKEN_REFILL_RATE,
    )

    return bool(allowed), float(remaining_tokens), int(retry_after)
