"""
Script para cargar datos de prueba en la base de datos
Crea videos en estado 'processed' para poder probar los endpoints públicos
"""
import asyncio
import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Agregar el directorio raíz al path (permite ejecutar el script directamente)
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_session, engine, Base, SessionLocal
from app.models.video import Video, VideoStatus
from app.models.vote import Vote

logger = logging.getLogger(__name__)


async def seed_videos():
    """Crea videos de prueba en estado processed"""

    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # Datos de prueba
        videos_data = [
            {
                "user_id": "carlos.martinez@example.com",
                "title": "Mate espectacular en bandeja",
                "player_first_name": "Carlos",
                "player_last_name": "Martínez",
                "player_city": "Medellín",
                "original_filename": "mate_bandeja.mp4",
                "original_path": "/uploads/demo_video_1.mp4",
                "processed_path": "/processed/demo_video_1_processed.mp4",
                "status": VideoStatus.processed,
                "file_size_mb": 15.2,
                "duration_seconds": 28,
            },
            {
                "user_id": "ana.rodriguez@example.com",
                "title": "Serie de tiros libres perfectos",
                "player_first_name": "Ana",
                "player_last_name": "Rodríguez",
                "player_city": "Bogotá",
                "original_filename": "tiros_libres.mp4",
                "original_path": "/uploads/demo_video_2.mp4",
                "processed_path": "/processed/demo_video_2_processed.mp4",
                "status": VideoStatus.processed,
                "file_size_mb": 12.8,
                "duration_seconds": 25,
            },
            {
                "user_id": "luis.garcia@example.com",
                "title": "Defensa y contraataque rápido",
                "player_first_name": "Luis",
                "player_last_name": "García",
                "player_city": "Cali",
                "original_filename": "contraataque.mp4",
                "original_path": "/uploads/demo_video_3.mp4",
                "processed_path": "/processed/demo_video_3_processed.mp4",
                "status": VideoStatus.processed,
                "file_size_mb": 18.5,
                "duration_seconds": 30,
            },
            {
                "user_id": "maria.lopez@example.com",
                "title": "Triple desde media cancha",
                "player_first_name": "María",
                "player_last_name": "López",
                "player_city": "Bogotá",
                "original_filename": "triple_largo.mp4",
                "original_path": "/uploads/demo_video_4.mp4",
                "processed_path": "/processed/demo_video_4_processed.mp4",
                "status": VideoStatus.processed,
                "file_size_mb": 14.3,
                "duration_seconds": 20,
            },
            {
                "user_id": "jorge.hernandez@example.com",
                "title": "Bloqueo defensivo impresionante",
                "player_first_name": "Jorge",
                "player_last_name": "Hernández",
                "player_city": "Medellín",
                "original_filename": "bloqueo.mp4",
                "original_path": "/uploads/demo_video_5.mp4",
                "processed_path": "/processed/demo_video_5_processed.mp4",
                "status": VideoStatus.processed,
                "file_size_mb": 16.7,
                "duration_seconds": 22,
            },
        ]

        created_videos = []
        logger.info("🎬 Creando videos de prueba...")

        for idx, video_data in enumerate(videos_data, 1):
            video = Video(
                **video_data,
                processed_at=datetime.now(timezone.utc) - timedelta(hours=idx),
            )
            session.add(video)
            created_videos.append(video)
            logger.info("  ✅ Video %s: %s - %s", idx, video_data["title"], video_data["player_city"])

        await session.commit()

        # Refrescar para obtener los IDs
        for video in created_videos:
            await session.refresh(video)

        logger.info("\n🗳️  Creando votos de prueba...")

        # Crear algunos votos de ejemplo
        votes_data = [
            # Video 1 (Carlos - Medellín): 5 votos
            {"video_id": created_videos[0].id, "user_id": "voter1@example.com"},
            {"video_id": created_videos[0].id, "user_id": "voter2@example.com"},
            {"video_id": created_videos[0].id, "user_id": "voter3@example.com"},
            {"video_id": created_videos[0].id, "user_id": "voter4@example.com"},
            {"video_id": created_videos[0].id, "user_id": "voter5@example.com"},
            
            # Video 2 (Ana - Bogotá): 3 votos
            {"video_id": created_videos[1].id, "user_id": "voter1@example.com"},
            {"video_id": created_videos[1].id, "user_id": "voter6@example.com"},
            {"video_id": created_videos[1].id, "user_id": "voter7@example.com"},
            
            # Video 3 (Luis - Cali): 2 votos
            {"video_id": created_videos[2].id, "user_id": "voter2@example.com"},
            {"video_id": created_videos[2].id, "user_id": "voter8@example.com"},
            
            # Video 4 (María - Bogotá): 7 votos
            {"video_id": created_videos[3].id, "user_id": "voter3@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter4@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter5@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter9@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter10@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter11@example.com"},
            {"video_id": created_videos[3].id, "user_id": "voter12@example.com"},
            
            # Video 5 (Jorge - Medellín): 4 votos
            {"video_id": created_videos[4].id, "user_id": "voter6@example.com"},
            {"video_id": created_videos[4].id, "user_id": "voter7@example.com"},
            {"video_id": created_videos[4].id, "user_id": "voter13@example.com"},
            {"video_id": created_videos[4].id, "user_id": "voter14@example.com"},
        ]

        for vote_data in votes_data:
            vote = Vote(**vote_data)
            session.add(vote)

        await session.commit()

        logger.info("  ✅ %s votos creados", len(votes_data))

        logger.info("\n✨ Datos de prueba cargados exitosamente!\n")
        logger.info("📊 Resumen:")
        logger.info("  - Videos procesados: %s", len(created_videos))
        logger.info("  - Ciudades: Bogotá (2), Medellín (2), Cali (1)")
        logger.info("  - Votos totales: %s", len(votes_data))
        logger.info("\n🔗 Prueba los endpoints:")
        logger.info("  - GET http://localhost:8080/api/public/videos")
        logger.info("  - GET http://localhost:8080/api/public/videos?city=Bogotá")
        logger.info("  - GET http://localhost:8080/api/public/rankings")


async def clear_data():
    """Limpia los datos de prueba"""
    async with SessionLocal() as session:
        from sqlalchemy import delete
        
        logger.info("🗑️  Limpiando datos de prueba...")

        # Eliminar votos primero (por FK constraint)
        await session.execute(delete(Vote))
        await session.commit()
        logger.info("  ✅ Votos eliminados")

        # Eliminar videos
        await session.execute(delete(Video))
        await session.commit()
        logger.info("  ✅ Videos eliminados")

        logger.info("✨ Base de datos limpiada\n")


if __name__ == "__main__":
    import sys
    import logging as _logging

    _logging.basicConfig(level=_logging.INFO)
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_data())
    else:
        asyncio.run(seed_videos())
