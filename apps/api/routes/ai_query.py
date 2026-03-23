from fastapi import APIRouter
from pydantic import BaseModel

from services.ai_service import process_ai_query

router = APIRouter()


class AIQueryRequest(BaseModel):
    query: str


class AIQueryResponse(BaseModel):
    query: str
    sql: str
    results: list[dict[str, str | int]]
    explanation: str


@router.post("/ai-query", response_model=AIQueryResponse)
def ai_query(request: AIQueryRequest) -> AIQueryResponse:
    result = process_ai_query(request.query)
    return AIQueryResponse(
        query=request.query,
        sql=result.sql,
        results=result.results,
        explanation=result.explanation,
    )
