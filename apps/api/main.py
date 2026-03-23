from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.seed import seed_database
from routes.search import router as search_router
from routes.ai_query import router as ai_query_router
from routes.metadata import router as metadata_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield


app = FastAPI(
    title="Genlogs API",
    description="Logistics analytics platform - freight movement tracking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, tags=["search"])
app.include_router(ai_query_router, tags=["ai"])
app.include_router(metadata_router, tags=["metadata"])


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "genlogs-api"}
