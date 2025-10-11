# ANB Rising Stars Showcase - API REST

API REST para la gestión de videos y votaciones de jugadores de baloncesto.

## Requisitos

- Python 3.12+
- Docker
- FastAPI

## Ejecución con Docker

**Nota:** El archivo `compose.yaml` está en la raíz del proyecto.

1. Desde la raíz del proyecto, construir e iniciar el contenedor:
```bash
docker-compose up --build
```
o puede iniciar la API directamente
```bash
docker compose up api --build
```

2. La API estará disponible en:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. Detener el contenedor:
```bash
docker-compose down
```

## Ejecución Local (Desarrollo)

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Mac
source venv\Scripts\activate  # En Windows 
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```

4. Ejecutar la aplicación:
Dev
```bash
fastapi dev main.py
```

Prod
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del Proyecto

```
APIRestful/
├── app/                   # Código fuente de la aplicación
│   ├── api/               # Endpoints (routers)
│   │   ├── auth.py        # Endpoints de autenticación
│   │   ├── videos.py      # Endpoints de gestión de videos
│   │   └── public.py      # Endpoints públicos
│   ├── schemas/           # Modelos Pydantic (request/response)
│   │   ├── auth.py        # Schemas de autenticación
│   │   ├── video.py       # Schemas de videos
│   │   ├── vote.py        # Schemas de votación
│   │   └── common.py      # Schemas comunes
│   ├── exceptions/        # Excepciones personalizadas
│   │   ├── custom_exceptions.py  # 18 excepciones específicas
│   │   └── handlers.py    # Handlers globales
│   ├── services/          # Lógica de negocio
│   ├── utils/             # Utilidades
│   └── config.py          # Configuración
├── tests/                 # Tests unitarios (72 tests)
├── storage/               # Almacenamiento de archivos
│   ├── uploads/           # Videos originales
│   └── processed/         # Videos procesados
├── Dockerfile             # Imagen Docker de la API
├── .dockerignore          # Exclusiones para Docker
├── requirements.txt       # Dependencias
├── pytest.ini             # Configuración de tests
└── main.py                # Punto de entrada
```

## Testing

# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app

# Ver reporte HTML de coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html

## Endpoints
Todos los endpoints están documentados en Swagger UI (http://localhost:8000/docs).
### Autenticación
- `POST /api/auth/signup` - Registro de jugadores
- `POST /api/auth/login` - Inicio de sesión

### Videos
- `POST /api/videos/upload` - Subir video
- `GET /api/videos` - Listar mis videos
- `GET /api/videos/{video_id}` - Detalle de video
- `DELETE /api/videos/{video_id}` - Eliminar video

### Público
- `GET /api/public/videos` - Listar videos públicos
- `POST /api/public/videos/{video_id}/vote` - Votar por video
- `GET /api/public/rankings` - Ranking de jugadores

# Storage
El sistema de almacenamiento usa volúmenes Docker para persistir archivos:

- `storage/uploads/`: Videos originales subidos por usuarios
- `storage/processed/`: Videos procesados (recortados, con marca de agua)

Los archivos persisten aunque se reinicien o eliminen los contenedores.

# Variables de Entorno
Ver `.env.example`
 para la lista completa de variables configurables.

## Principales:
- `APP_NAME`: Nombre de la aplicación
- `DEBUG`: Modo debug (True/False)
- `MAX_UPLOAD_SIZE_MB`: Tamaño máximo de archivos (100MB)
- `ALLOWED_VIDEO_FORMATS`: Formatos permitidos (mp4, avi, mov)
- `MIN_VIDEO_DURATION_SECONDS`: Duración mínima (20s)
- `MAX_VIDEO_DURATION_SECONDS`: Duración máxima (60s)