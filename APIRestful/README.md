# ANB Rising Stars Showcase - API REST

API REST para la gestión de videos y votaciones de jugadores de baloncesto.

## Requisitos

- Python 3.12+
- FastAPI
- Uvicorn

## Instalación

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```

## Ejecución

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del Proyecto

```
APIRestful/
├── app/                    # Código fuente de la aplicación
│   ├── api/               # Endpoints (routers)
│   ├── schemas/           # Modelos Pydantic (request/response)
│   ├── services/          # Lógica de negocio
│   ├── utils/             # Utilidades
│   └── exceptions/        # Excepciones personalizadas
├── tests/                 # Tests unitarios
├── storage/               # Almacenamiento de archivos
└── requirements.txt       # Dependencias
```

## Testing

```bash
pytest
```

## Endpoints

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
