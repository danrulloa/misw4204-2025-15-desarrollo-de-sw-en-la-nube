from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
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
    """
    Gestiona el ciclo de vida de la aplicación.
    Se ejecuta al iniciar la aplicación para crear las tablas de la base de datos
    y al finalizar para realizar tareas de limpieza si es necesario.
    """
    # Crear todas las tablas definidas en los modelos al iniciar la aplicación
    Base.metadata.create_all(bind=engine)
    yield
    # Aquí se pueden agregar tareas de limpieza al cerrar la aplicación


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    description="API REST para la gestión de videos y votaciones de jugadores de baloncesto",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configurar orígenes específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Importar y registrar routers
from app.api import auth, videos, public

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(public.router)


@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "ANB Rising Stars Showcase API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {"status": "healthy"}