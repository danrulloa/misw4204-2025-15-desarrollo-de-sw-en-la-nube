from fastapi import Request, HTTPException
from fastapi.routing import APIRoute
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

ACCESS_TOKEN_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Rutas públicas que no requieren autenticación
EXCLUDED_PATHS = {"/api/v1/login", "api/v1/register","/api/v1/refresh", "/docs", "/openapi.json", "/api/v1/status"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Omitir rutas excluidas
        path=request.url.path
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header[len("Bearer "):]

        try:
            payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
            # Guardar información del usuario en el request.state
            request.state.user = {
                "username": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "tenant_id": payload.get("tenant_id"),
                "permissions": payload.get("permissions", [])
            }
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return await call_next(request)