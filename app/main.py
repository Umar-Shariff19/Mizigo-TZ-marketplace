from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import generic_exception_handler, http_exception_handler
from app.db.database import Base, engine
from app.routers import admin, auth, orders, payments, products, users, vendors

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mizigo TZ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
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
