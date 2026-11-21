from fastapi import FastAPI
from routers.claims import router as claims_router
from routers.auth import router as auth_router

app = FastAPI(
    title="Insurance Claims",
    description="API for managing Motor, HealthClaim and Property Insurance Claims",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Insurance Claims",
        "supported_categories": ["Motor", "Health", "Property"],
    }


app.include_router(claims_router, prefix="/claims", tags=["Claims"])

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
