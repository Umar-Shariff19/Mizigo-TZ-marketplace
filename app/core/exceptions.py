from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.services.image_service import delete_image_file

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # If product creation fails validation, ensure uploaded image is not left orphaned
    if request.url.path == "/products" and request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict) and body.get("image_url"):
                delete_image_file(body["image_url"])
        except Exception:
            pass

    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation Error",
            "detail": jsonable_encoder(exc.errors()),
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "detail": exc.detail
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal Server Error",
            "detail": "Internal Server Error"
        }
    )
