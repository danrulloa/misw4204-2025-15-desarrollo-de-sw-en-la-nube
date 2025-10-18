from fastapi import Request
from starlette.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

ACCESS_TOKEN_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

EXCLUDED_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/docs/oauth2-redirect",
    "/nginx-health"
}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in EXCLUDED_PATHS:
            return await call_next(request)

        public_prefixes = ("/docs", "/redoc", "/openapi", "/public")
        if any(path.startswith(prefix) for prefix in public_prefixes):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"}
            )

        token = auth_header[len("Bearer "):]

        try:
            payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = {
                "username": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "tenant_id": payload.get("tenant_id"),
                "permissions": payload.get("permissions", []),
                "first_name": payload.get("first_name", ""),
                "last_name": payload.get("last_name", ""),
                "city": payload.get("city", "")
            }
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )

        return await call_next(request)