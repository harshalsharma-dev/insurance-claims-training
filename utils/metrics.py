from prometheus_client import Counter, Histogram

# Total number of HTTP requests
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

# HTTP request processing duration
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
)
