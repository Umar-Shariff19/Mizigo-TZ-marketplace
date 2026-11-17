import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from fastapi import HTTPException, UploadFile
from app.core.config import settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 64 * 1024  # 64 KB read buffer
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/pjpeg",
}


def _detect_image_extension(contents: bytes) -> str | None:
    """Detect image format by sniffing magic bytes."""
    if len(contents) >= 3 and contents[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if len(contents) >= 8 and contents[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_product_image(file: UploadFile) -> str:
    """
    Validate and persist a product image upload.
    Enforces format, extension, MIME type, and size constraints while reading.
    Returns relative URL path (e.g. /uploads/products/<unique_id>.png).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # 1. Extension validation
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: JPEG, PNG, WebP"
        )

    # 2. Content-Type MIME validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image MIME type '{file.content_type}'. Allowed MIME types: image/jpeg, image/png, image/webp"
        )

    # 3. Size validation enforced while reading chunk-by-chunk
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Image size exceeds the maximum allowed limit of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB"
            )
        chunks.append(chunk)

    if total_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    contents = b"".join(chunks)

    # 4. Content magic bytes verification
    canonical_ext = _detect_image_extension(contents)
    if not canonical_ext:
        raise HTTPException(
            status_code=400,
            detail="File content does not match a valid supported image format (JPEG, PNG, WebP)"
        )

    # If the user provided .jpeg, map to .jpg or keep canonical
    if ext in {".jpg", ".jpeg"} and canonical_ext == ".jpg":
        saved_ext = ext
    else:
        saved_ext = canonical_ext

    # 5. Ensure storage directory exists
    product_dir = Path(settings.PRODUCT_UPLOAD_DIR)
    product_dir.mkdir(parents=True, exist_ok=True)

    # 6. Generate collision-resistant unique filename
    unique_filename = f"{uuid.uuid4().hex}{saved_ext}"
    target_path = product_dir / unique_filename
    while target_path.exists():
        unique_filename = f"{uuid.uuid4().hex}{saved_ext}"
        target_path = product_dir / unique_filename

    # 7. Write securely to local storage
    with open(target_path, "wb") as f:
        f.write(contents)

    # 8. Return relative URL path
    return f"/uploads/products/{unique_filename}"


def delete_image_file(image_url: str | None, db: "Session | None" = None) -> None:
    """Safely delete an existing image file from storage if present and unreferenced."""
    if not image_url or not image_url.startswith("/uploads/products/"):
        return

    # Check if another product still references this image
    if db is not None:
        from app.models.product import Product
        still_referenced = db.query(Product).filter(Product.image_url == image_url).first()
        if still_referenced:
            return

    filename = os.path.basename(image_url)
    target_path = Path(settings.PRODUCT_UPLOAD_DIR) / filename
    try:
        if target_path.is_file():
            target_path.unlink()
    except OSError:
        pass
