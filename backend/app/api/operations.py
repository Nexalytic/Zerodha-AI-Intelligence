from fastapi import APIRouter

from app.demo_store import get_operations_metrics


router = APIRouter(
    prefix="/api/v1/operations",
    tags=["operations"],
)


@router.get("/metrics")
def operations_metrics() -> dict:
    return get_operations_metrics()