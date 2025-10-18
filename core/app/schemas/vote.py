from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class VoteResponse(BaseModel):
    """Schema para respuesta de votación"""
    message: str = Field(..., description="Mensaje de confirmación")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Voto registrado exitosamente."
            }
        }


class PublicVideoResponse(BaseModel):
    """Schema para videos públicos disponibles para votación"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "video_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "title": "Tiros de tres en movimiento",
                "player_name": "Pedro López",
                "city": "Bogotá",
                "processed_url": None,
                "votes": 125
            }
        }
    )
    
    video_id: str = Field(..., description="ID único del video")
    title: str = Field(..., description="Título del video")
    player_name: str = Field(..., description="Nombre del jugador", alias="username")
    city: str = Field(..., description="Ciudad del jugador")
    processed_url: Optional[str] = Field(None, description="URL del video procesado")
    votes: int = Field(default=0, description="Número de votos recibidos")


class RankingItemResponse(BaseModel):
    """Schema para un item en el ranking"""
    position: int = Field(..., description="Posición en el ranking")
    username: str = Field(..., description="Nombre del jugador")
    city: str = Field(..., description="Ciudad del jugador")
    votes: int = Field(..., description="Total de votos recibidos")

    class Config:
        json_schema_extra = {
            "example": {
                "position": 1,
                "username": "Pedro López",
                "city": "Bogotá",
                "votes": 1530
            }
        }


class RankingResponse(BaseModel):
    """Schema para la respuesta del ranking"""
    rankings: List[RankingItemResponse] = Field(..., description="Lista de jugadores en el ranking")
    total: int = Field(..., description="Total de jugadores en el ranking")

    class Config:
        json_schema_extra = {
            "example": {
                "rankings": [
                    {
                        "position": 1,
                        "username": "Pedro López",
                        "city": "Bogotá",
                        "votes": 1530
                    },
                    {
                        "position": 2,
                        "username": "Ana Martínez",
                        "city": "Medellín",
                        "votes": 1495
                    }
                ],
                "total": 2
            }
        }
