# 🌱 Script de Datos de Prueba (Seed Data)

Este script carga datos de prueba en la base de datos para poder probar los endpoints públicos sin necesidad de tener el worker funcionando.

## 📋 ¿Qué hace?

El script `seed_data.py` crea:
- **5 videos** en estado `processed` con datos realistas
- **21 votos** distribuidos entre los videos
- Jugadores de **3 ciudades** diferentes: Bogotá, Medellín, Cali

## 🚀 Cómo usar

### Opción 1: Desde el contenedor (Recomendado)

```powershell
# Cargar datos de prueba
docker compose exec anb_api python seed_data.py

# Limpiar datos de prueba
docker compose exec anb_api python seed_data.py --clear
```

### Opción 2: Desde tu máquina local

```powershell
# Navega a la carpeta core
cd core

# Activa el entorno virtual (si lo tienes)
# .\.venv\Scripts\Activate.ps1

# Ejecuta el script
python seed_data.py

# Para limpiar
python seed_data.py --clear
```

## 📊 Datos creados

### Videos (todos en estado `processed`)

1. **Carlos Martínez** (Medellín) - "Mate espectacular en bandeja" → 5 votos
2. **Ana Rodríguez** (Bogotá) - "Serie de tiros libres perfectos" → 3 votos
3. **Luis García** (Cali) - "Defensa y contraataque rápido" → 2 votos
4. **María López** (Bogotá) - "Triple desde media cancha" → 7 votos ⭐ (más votado)
5. **Jorge Hernández** (Medellín) - "Bloqueo defensivo impresionante" → 4 votos

### Distribución por ciudad

- **Bogotá**: 2 videos (10 votos totales)
- **Medellín**: 2 videos (9 votos totales)
- **Cali**: 1 video (2 votos)

## 🧪 Endpoints para probar

Después de cargar los datos, prueba:

```powershell
# Listar todos los videos públicos
Invoke-RestMethod "http://localhost:8080/api/public/videos"

# Filtrar por ciudad
Invoke-RestMethod "http://localhost:8080/api/public/videos?city=Bogotá"

# Ver ranking global
Invoke-RestMethod "http://localhost:8080/api/public/rankings"

# Ranking por ciudad
Invoke-RestMethod "http://localhost:8080/api/public/rankings?city=Medellín"
```

## ⚠️ Notas importantes

- Este script **NO elimina** datos existentes al ejecutarse (solo agrega)
- Usa `--clear` para limpiar **todos** los videos y votos
- Los archivos de video mencionados no existen realmente (son solo referencias en BD)
- Los `user_id` de los videos son emails de prueba que no existen en el sistema de autenticación

## 🔄 Workflow recomendado

1. **Primera vez**: Ejecuta el script para tener datos de prueba
2. **Desarrollo**: Trabaja con estos datos para probar endpoints públicos
3. **Limpiar**: Usa `--clear` cuando necesites resetear
4. **Producción**: NO ejecutes este script en producción

## 💡 Personalizar

Para agregar más datos de prueba, edita el array `videos_data` en `seed_data.py`:

```python
{
    "user_id": "tu_email@example.com",
    "title": "Título del video",
    "player_first_name": "Nombre",
    "player_last_name": "Apellido",
    "player_city": "Ciudad",
    "original_filename": "archivo.mp4",
    "original_path": "/uploads/tu_video.mp4",
    "processed_path": "/processed/tu_video_processed.mp4",
    "status": VideoStatus.processed,
    "file_size_mb": 15.0,
    "duration_seconds": 25,
}
```
