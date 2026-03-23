from fastapi import APIRouter
from pydantic import BaseModel

from services.search_service import search_carriers

router = APIRouter()


class SearchRequest(BaseModel):
    origin: str
    destination: str


class CarrierResponse(BaseModel):
    carrier_name: str
    trucks_per_day: int


class SearchResponse(BaseModel):
    origin: str
    destination: str
    carriers: list[CarrierResponse]
    total_carriers: int


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    results = search_carriers(request.origin, request.destination)
    return SearchResponse(
        origin=request.origin,
        destination=request.destination,
        carriers=[
            CarrierResponse(
                carrier_name=r.carrier_name,
                trucks_per_day=r.trucks_per_day,
            )
            for r in results
        ],
        total_carriers=len(results),
    )
