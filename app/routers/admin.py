from fastapi import APIRouter, Depends

from app.core.deps import require_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_user)],
)


@router.get(
    "/status",
    summary="Admin status",
    description="Confirms that the authenticated user has access to the admin module.",
)
def admin_status() -> dict:
    return {"status": "ok"}
