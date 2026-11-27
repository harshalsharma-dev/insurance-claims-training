import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.claims import router as claims_router

logger = logging.getLogger("uvicorn.error")


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
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    logger.info(
        "%s %s - Status: %s - Process Time: %.4f seconds",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )

    return response


@app.get("/")
def home():
    return {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(claims_router, prefix="/claims", tags=["Claims"])

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
