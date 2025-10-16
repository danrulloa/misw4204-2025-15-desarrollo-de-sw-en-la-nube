"""
Script para cargar datos de prueba en la base de datos
Crea videos en estado 'processed' para poder probar los endpoints públicos
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_session, engine, Base
from app.models.video import Video, VideoStatus
from app.models.vote import Vote


async def seed_videos():
    """Crea videos de prueba en estado processed"""
    
    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async for session in get_session():
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
        print("🎬 Creando videos de prueba...")
        
        for idx, video_data in enumerate(videos_data, 1):
            video = Video(
                **video_data,
                processed_at=datetime.utcnow() - timedelta(hours=idx)
            )
            session.add(video)
            created_videos.append(video)
            print(f"  ✅ Video {idx}: {video_data['title']} - {video_data['player_city']}")
        
        await session.commit()
        
        # Refrescar para obtener los IDs
        for video in created_videos:
            await session.refresh(video)
        
        print(f"\n🗳️  Creando votos de prueba...")
        
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
        
        print(f"  ✅ {len(votes_data)} votos creados")
        
        print("\n✨ Datos de prueba cargados exitosamente!\n")
        print("📊 Resumen:")
        print(f"  - Videos procesados: {len(created_videos)}")
        print(f"  - Ciudades: Bogotá (2), Medellín (2), Cali (1)")
        print(f"  - Votos totales: {len(votes_data)}")
        print("\n🔗 Prueba los endpoints:")
        print("  - GET http://localhost:8080/api/public/videos")
        print("  - GET http://localhost:8080/api/public/videos?city=Bogotá")
        print("  - GET http://localhost:8080/api/public/rankings")
        
        break  # Solo necesitamos una sesión


async def clear_data():
    """Limpia los datos de prueba"""
    async for session in get_session():
        from sqlalchemy import delete
        
        print("🗑️  Limpiando datos de prueba...")
        
        # Eliminar votos primero (por FK constraint)
        await session.execute(delete(Vote))
        await session.commit()
        print("  ✅ Votos eliminados")
        
        # Eliminar videos
        await session.execute(delete(Video))
        await session.commit()
        print("  ✅ Videos eliminados")
        
        print("✨ Base de datos limpiada\n")
        break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_data())
    else:
        asyncio.run(seed_videos())
