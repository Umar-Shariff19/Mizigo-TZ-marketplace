import io
import os
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from tests.conftest import TestingSessionLocal, TEST_UPLOAD_DIR

client = TestClient(app)

# Minimal valid magic bytes for test fixtures
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
VALID_WEBP_BYTES = b"RIFF\x1a\x00\x00\x00WEBPVP8L\x0e\x00\x00\x00/\x00\x00\x00\x00\x07\x88\x81\x08\x88\x88\x08\x00\x00"


@pytest.fixture
def auth_fixture():
    """Create test users: vendor A, vendor B, and customer."""
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user_a = User(
            email=f"vendor_a_{uid}@mizigo.com",
            hashed_password=hash_password("pass123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        user_b = User(
            email=f"vendor_b_{uid}@mizigo.com",
            hashed_password=hash_password("pass123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        customer = User(
            email=f"cust_{uid}@mizigo.com",
            hashed_password=hash_password("pass123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add_all([user_a, user_b, customer])
        db.commit()

        vendor_a = Vendor(user_id=user_a.id, store_name=f"Store A {uid}", is_active=True)
        vendor_b = Vendor(user_id=user_b.id, store_name=f"Store B {uid}", is_active=True)
        db.add_all([vendor_a, vendor_b])
        db.commit()

        token_a = create_access_token(data={"sub": user_a.email, "role": user_a.role})
        token_b = create_access_token(data={"sub": user_b.email, "role": user_b.role})
        token_cust = create_access_token(data={"sub": customer.email, "role": customer.role})

        return {
            "token_a": token_a,
            "token_b": token_b,
            "token_cust": token_cust,
            "vendor_a_id": vendor_a.id,
            "vendor_b_id": vendor_b.id,
        }
    finally:
        db.close()


def test_successful_vendor_image_upload(auth_fixture):
    """Test vendor can upload valid JPEG, PNG, and WebP images."""
    token = auth_fixture["token_a"]

    # 1. JPEG upload
    res_jpeg = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")},
    )
    assert res_jpeg.status_code == 200
    data_jpeg = res_jpeg.json()
    assert "image_url" in data_jpeg
    assert data_jpeg["image_url"].startswith("/uploads/products/")
    assert data_jpeg["image_url"].endswith(".jpg")

    # Verify stored in isolated test storage, NOT real uploads directory
    saved_filename = os.path.basename(data_jpeg["image_url"])
    saved_file_path = os.path.join(TEST_UPLOAD_DIR, "products", saved_filename)
    assert os.path.isfile(saved_file_path)

    # 2. PNG upload
    res_png = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("sample.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert res_png.status_code == 200
    assert res_png.json()["image_url"].endswith(".png")

    # 3. WebP upload
    res_webp = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("graphic.webp", io.BytesIO(VALID_WEBP_BYTES), "image/webp")},
    )
    assert res_webp.status_code == 200
    assert res_webp.json()["image_url"].endswith(".webp")


def test_rejection_of_unsupported_file_formats(auth_fixture):
    """Reject invalid file extensions, spoofed MIME types, and corrupt binaries."""
    token = auth_fixture["token_a"]

    # 1. Plain text file with .txt extension
    res_txt = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", io.BytesIO(b"Hello world text"), "text/plain")},
    )
    assert res_txt.status_code == 400
    assert "Unsupported file extension" in res_txt.json()["detail"]

    # 2. Executable disguised with .jpg extension and image/jpeg MIME
    fake_jpeg = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    res_fake = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malware.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
    )
    assert res_fake.status_code == 400
    assert "File content does not match" in res_fake.json()["detail"]

    # 3. Unsupported image format (GIF)
    gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    res_gif = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("animation.gif", io.BytesIO(gif_bytes), "image/gif")},
    )
    assert res_gif.status_code == 400
    assert "Unsupported file extension" in res_gif.json()["detail"]

    # 4. Empty file
    res_empty = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"].lower()


def test_rejection_of_files_exceeding_size_limit(auth_fixture):
    """Reject files larger than 5 MB."""
    token = auth_fixture["token_a"]

    # Construct payload of 5 MB + 1024 bytes with valid JPEG header
    oversized = io.BytesIO(b"\xff\xd8\xff\xe0" + b"A" * (5 * 1024 * 1024 + 1024))
    res = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("large_photo.jpg", oversized, "image/jpeg")},
    )
    assert res.status_code == 400
    assert "maximum allowed limit" in res.json()["detail"]


def test_unauthorized_upload_attempts(auth_fixture):
    """Unauthenticated users and non-vendors cannot upload images."""
    cust_token = auth_fixture["token_cust"]

    # 1. No Authorization header
    res_unauth = client.post(
        "/products/upload-image",
        files={"file": ("photo.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")},
    )
    assert res_unauth.status_code == 401

    # 2. Customer user attempting upload
    res_cust = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("photo.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")},
    )
    assert res_cust.status_code == 403
    assert "vendor" in res_cust.json()["detail"].lower()


def test_product_creation_with_image_and_catalogue_response(auth_fixture):
    """Image URL is stored upon product creation and returned in all responses."""
    token = auth_fixture["token_a"]

    # First upload an image
    upload_res = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("product_item.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert upload_res.status_code == 200
    image_url = upload_res.json()["image_url"]

    # Create product with the uploaded image URL
    create_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Handmade Tanzanian Basket",
            "description": "Authentic woven basket from Arusha",
            "price": "35.50",
            "quantity": 12,
            "image_url": image_url,
        },
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["image_url"] == image_url
    product_id = created["id"]

    # Check GET /products/{id}
    detail_res = client.get(f"/products/{product_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["image_url"] == image_url

    # Check GET /products (catalogue)
    cat_res = client.get("/products")
    assert cat_res.status_code == 200
    found = [p for p in cat_res.json() if p["id"] == product_id]
    assert len(found) == 1
    assert found[0]["image_url"] == image_url

    # Check GET /vendor/products
    vp_res = client.get("/vendor/products", headers={"Authorization": f"Bearer {token}"})
    assert vp_res.status_code == 200
    vp_found = [p for p in vp_res.json() if p["id"] == product_id]
    assert len(vp_found) == 1
    assert vp_found[0]["image_url"] == image_url


def test_existing_products_without_images_still_work(auth_fixture):
    """Products created without an image work seamlessly and have image_url as null."""
    token = auth_fixture["token_a"]

    create_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Standard Product No Image",
            "price": "19.99",
            "quantity": 5,
        },
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["image_url"] is None

    detail_res = client.get(f"/products/{created['id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["image_url"] is None


def test_product_image_replacement_and_ownership_checks(auth_fixture):
    """Vendors can replace images on their own products but cannot modify others' products."""
    token_a = auth_fixture["token_a"]
    token_b = auth_fixture["token_b"]

    # Vendor A creates a product
    create_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Vendor A Product", "price": "50.00", "quantity": 10},
    )
    assert create_res.status_code == 200
    product_id = create_res.json()["id"]

    # Vendor A uploads image 1 directly to the product
    res1 = client.post(
        f"/vendor/products/{product_id}/image",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("img1.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")},
    )
    assert res1.status_code == 200
    url1 = res1.json()["image_url"]
    assert url1.endswith(".jpg")

    # Vendor B attempts to replace image on Vendor A's product -> 403 Forbidden
    res_b_attack = client.post(
        f"/vendor/products/{product_id}/image",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("hacked.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert res_b_attack.status_code == 403
    assert "Not authorized" in res_b_attack.json()["detail"]

    # Vendor A replaces image with image 2
    res2 = client.post(
        f"/vendor/products/{product_id}/image",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("img2.webp", io.BytesIO(VALID_WEBP_BYTES), "image/webp")},
    )
    assert res2.status_code == 200
    url2 = res2.json()["image_url"]
    assert url2.endswith(".webp")
    assert url2 != url1

    # Vendor B attempts to remove image from Vendor A's product -> 403 Forbidden
    del_b = client.delete(
        f"/vendor/products/{product_id}/image",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_b.status_code == 403

    # Vendor A removes image -> 200, image_url is null
    del_a = client.delete(
        f"/vendor/products/{product_id}/image",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_a.status_code == 200
    assert del_a.json()["image_url"] is None


def test_static_file_serving(auth_fixture):
    """Uploaded images are served via FastAPI static file mount."""
    token = auth_fixture["token_a"]

    res = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_pic.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert res.status_code == 200
    image_url = res.json()["image_url"]

    # Request the static file via GET
    file_res = client.get(image_url)
    assert file_res.status_code == 200
    assert file_res.content == VALID_PNG_BYTES


def test_failed_product_creation_cleans_up_orphaned_image(auth_fixture):
    """If product creation fails validation, the uploaded image must not remain orphaned."""
    token = auth_fixture["token_a"]

    # 1. Upload valid image
    up_res = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("orphan_candidate.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert up_res.status_code == 200
    image_url = up_res.json()["image_url"]

    filename = os.path.basename(image_url)
    file_path = os.path.join(TEST_UPLOAD_DIR, "products", filename)
    assert os.path.isfile(file_path)

    # 2. Try to create product with invalid negative price -> 400
    bad_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Invalid Price Item",
            "price": "-10.00",
            "quantity": 5,
            "image_url": image_url,
        },
    )
    assert bad_res.status_code == 422 or bad_res.status_code == 400

    # 3. Verify the orphaned file was deleted from disk
    assert not os.path.exists(file_path)


def test_shared_image_not_deleted_if_referenced_by_another_product(auth_fixture):
    """Deleting a product must not delete the image file if another product still references it."""
    token = auth_fixture["token_a"]

    # 1. Upload image
    up_res = client.post(
        "/products/upload-image",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("shared_pic.png", io.BytesIO(VALID_PNG_BYTES), "image/png")},
    )
    assert up_res.status_code == 200
    image_url = up_res.json()["image_url"]

    filename = os.path.basename(image_url)
    file_path = os.path.join(TEST_UPLOAD_DIR, "products", filename)
    assert os.path.isfile(file_path)

    # 2. Create Product 1 and Product 2 sharing the same image_url
    p1_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Product One", "price": "25.00", "quantity": 10, "image_url": image_url},
    )
    assert p1_res.status_code == 200
    p1_id = p1_res.json()["id"]

    p2_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Product Two", "price": "30.00", "quantity": 5, "image_url": image_url},
    )
    assert p2_res.status_code == 200
    p2_id = p2_res.json()["id"]

    # 3. Delete Product 1
    del1 = client.delete(f"/vendor/products/{p1_id}", headers={"Authorization": f"Bearer {token}"})
    assert del1.status_code == 200

    # File MUST still exist on disk because Product 2 references it
    assert os.path.isfile(file_path)

    # 4. Delete Product 2
    del2 = client.delete(f"/vendor/products/{p2_id}", headers={"Authorization": f"Bearer {token}"})
    assert del2.status_code == 200

    # Now that no other product references it, file should be safely deleted
    assert not os.path.exists(file_path)


def test_image_url_path_traversal_rejected_by_schema(auth_fixture):
    """Pydantic schema must reject path traversal sequences and unauthorized directory paths."""
    token = auth_fixture["token_a"]

    # Path traversal with ..
    res_trav = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Traversal Test", "price": "15.00", "quantity": 1, "image_url": "../../etc/shadow"},
    )
    assert res_trav.status_code == 422

    # Wrong upload directory
    res_wrong_dir = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Dir Test", "price": "15.00", "quantity": 1, "image_url": "/uploads/system/key.pem"},
    )
    assert res_wrong_dir.status_code == 422

