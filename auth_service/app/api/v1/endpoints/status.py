from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/status", tags=["Status"])
async def get_status():
    return JSONResponse(content={"status": "ok", "message": "Auth service is running 🚀"})
