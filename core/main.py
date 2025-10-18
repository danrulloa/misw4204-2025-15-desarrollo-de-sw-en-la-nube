from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.core.auth_middleware import AuthMiddleware

from app.config import settings
from app.database import Base, engine
from app.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    root_path="/api",
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="API REST para la gestión de videos y votaciones de jugadores de baloncesto",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"url": "./openapi.json"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

from app.api import videos, public, auth  # noqa: E402

app.include_router(videos.router)
app.include_router(public.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "ANB Rising Stars Showcase API",
        "version": settings.API_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {"status": "healthy"}
