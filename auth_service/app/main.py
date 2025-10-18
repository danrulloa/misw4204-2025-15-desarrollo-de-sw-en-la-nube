from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import api_router
from app.db.session import init_db, close_db
from app.core.auth_middleware import AuthMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          
    try:
        yield
    finally:
        await close_db()  

app = FastAPI(
    lifespan=lifespan,
    title="ANB Auth Service",
    version="1.0.0",
    docs_url="/auth/docs",
    redoc_url="/auth/redoc",
    openapi_url="/auth/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(AuthMiddleware) 

app.include_router(api_router, prefix="/auth/api/v1")

@app.on_event("startup")
async def _startup():
    Instrumentator().instrument(app).expose(app, endpoint="/auth/metrics", include_in_schema=False)
