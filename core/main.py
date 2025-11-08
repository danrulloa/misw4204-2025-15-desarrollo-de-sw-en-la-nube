from fastapi import FastAPI
import logging
from logging import StreamHandler, Formatter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator


from app.core.auth_middleware import AuthMiddleware
from app.core.metrics import MetricsMiddleware
from app.config import settings
from app.database import Base, engine
from app.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.observability.logging_filters import install_uvicorn_access_filter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await engine.dispose()

# Instala un filtro para suprimir logs de acceso de /health y /metrics
install_uvicorn_access_filter()

# Asegura que los logs de la app (anb.*) se vean a nivel INFO usando el handler de Uvicorn
_uvicorn_err_logger = logging.getLogger("uvicorn.error")
_app_base_logger = logging.getLogger("anb")
if _uvicorn_err_logger.handlers:
    # Reutiliza los handlers de Uvicorn si ya están disponibles
    _app_base_logger.handlers = _uvicorn_err_logger.handlers
    _app_base_logger.setLevel(logging.INFO)
    _app_base_logger.propagate = False
else:
    # Fallback: asegura un handler a stdout para 'anb' si Uvicorn aún no configuró logging
    fallback_handler = StreamHandler()
    fallback_handler.setFormatter(Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    _app_base_logger.addHandler(fallback_handler)
    _app_base_logger.setLevel(logging.INFO)
    _app_base_logger.propagate = False

app = FastAPI(
    root_path="/api",
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="API REST para la gestión de videos y votaciones de jugadores de baloncesto",
    docs_url="/docs",        
    redoc_url="/redoc",       
    openapi_url="/openapi.json",
    swagger_ui_parameters={"url": "./openapi.json"},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(MetricsMiddleware)

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Tracing deshabilitado (Tempo retirado)

from app.api import videos, public, auth
app.include_router(videos.router)
app.include_router(public.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "ANB Rising Stars Showcase API", "version": settings.API_VERSION, "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Configure Instrumentator with extended buckets to capture large request durations
# Try to pass 'buckets' when supported; fall back to default Instrumentator otherwise.
buckets = [
    0.001, 0.005, 0.01, 0.025, 0.05,
    0.1, 0.25, 0.5, 1, 2.5,
    5, 10, 30, 60, 120,
]
try:
    _instrumentator = Instrumentator(buckets=buckets)
except TypeError:
    # older version of the library doesn't accept 'buckets'
    _instrumentator = Instrumentator()

_instrumentator.instrument(app)
_instrumentator.expose(
    app,
    endpoint="/metrics",
    include_in_schema=False
)
