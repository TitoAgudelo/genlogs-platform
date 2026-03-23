from fastapi import APIRouter

from data.trips import get_unique_cities, get_unique_routes

router = APIRouter()


@router.get("/cities")
def list_cities() -> dict[str, list[str]]:
    return {"cities": get_unique_cities()}


@router.get("/routes")
def list_routes() -> dict[str, list[dict[str, str]]]:
    return {"routes": get_unique_routes()}
