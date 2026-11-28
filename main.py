import logging
import time
import uuid

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sqlalchemy import text

from config import settings
from database import engine
from routers.auth import router as auth_router
from routers.claims import router as claims_router
from utils.logging_config import configure_logging
from utils.metrics import REQUEST_COUNT, REQUEST_LATENCY
from utils.request_context import request_id_context
from utils.token_blocklist import redis_client

configure_logging()

logger = logging.getLogger(__name__)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )

from config import settings

DATABASE_URL = settings.database_url


app = FastAPI(
    title="Insurance Claims",
    description="API for managing Motor, HealthClaim and Property Insurance Claims",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware
@app.middleware("http")
async def logging_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request_id_token = request_id_context.set(request_id)
    start_time = time.perf_counter()

    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        process_time = time.perf_counter() - start_time

        logger.info(
            "%s %s - Status: %s - Process Time: %.4f seconds",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        logger.exception("Unhandled exception while processing request")

        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
        response.headers["X-Request-ID"] = request_id

        return response

    finally:
        process_time = time.perf_counter() - start_time

        route = request.scope.get("route")
        endpoint = getattr(route, "path", request.url.path)

        # Avoid counting Prometheus scraping requests
        if request.url.path != "/metrics":
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(process_time)

        request_id_context.reset(request_id_token)


@app.get("/")
def home():
    return {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/ready")
def readiness_check():
    checks = {
        "database": "healthy",
        "redis": "healthy",
    }

    # Check PostgreSQL connectivity
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "unhealthy"
        logger.exception("PostgreSQL readiness check failed")

    # Check Redis connectivity
    try:
        redis_client.ping()
    except Exception:
        checks["redis"] = "unhealthy"
        logger.exception("Redis readiness check failed")

    is_ready = all(status == "healthy" for status in checks.values())

    response = {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
    }

    if not is_ready:
        return JSONResponse(
            status_code=503,
            content=response,
        )

    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(claims_router, prefix="/claims", tags=["Claims"])

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
