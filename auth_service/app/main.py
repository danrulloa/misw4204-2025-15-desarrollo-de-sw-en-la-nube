from fastapi import FastAPI
from app.api.v1 import api_router
from app.db.session import init_db, close_db  
from contextlib import asynccontextmanager
from app.core.auth_middleware import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento de arranque
    await init_db()
    yield
    # Evento de apagado
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
    allow_credentials=True,         
    allow_methods=["*"],            
    allow_headers=["*"],            
    expose_headers=["*"]
)
app.add_middleware(AuthMiddleware)

app.include_router(api_router, prefix="/auth/api/v1")
