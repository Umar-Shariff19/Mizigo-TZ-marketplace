from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routers import admin, auth, orders, payments, products, users, vendors

# Ensure product upload storage directory exists
Path(settings.PRODUCT_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Mizigo TZ API")

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.state.limiter = auth.limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests"}
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns the API health status.",
)
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(vendors.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
