from pydantic import BaseModel, Field
from typing import List


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
    video_id: str = Field(..., description="ID único del video")
    title: str = Field(..., description="Título del video")
    player_name: str = Field(..., description="Nombre del jugador")
    city: str = Field(..., description="Ciudad del jugador")
    processed_url: str = Field(..., description="URL del video procesado")
    votes: int = Field(default=0, description="Número de votos recibidos")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "a1b2c3d4",
                "title": "Tiros de tres en movimiento",
                "player_name": "John Doe",
                "city": "Bogotá",
                "processed_url": "https://anb.com/processed/a1b2c3d4.mp4",
                "votes": 125
            }
        }


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
                "username": "superplayer",
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
                        "username": "superplayer",
                        "city": "Bogotá",
                        "votes": 1530
                    },
                    {
                        "position": 2,
                        "username": "nextstar",
                        "city": "Bogotá",
                        "votes": 1495
                    }
                ],
                "total": 2
            }
        }
