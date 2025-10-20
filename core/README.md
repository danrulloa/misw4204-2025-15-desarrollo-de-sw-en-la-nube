# ANB Rising Stars Showcase - API REST (Core)

Servicio principal del sistema ANB Rising Stars Showcase. API REST para la gestión de videos de jugadores de baloncesto y sistema de votaciones.

**Este servicio es parte de un sistema completo. Ver [README principal](../README.md) para instrucciones de despliegue e información general del proyecto.**

## Descripción

API REST desarrollada con FastAPI que proporciona:

- Gestión de videos (subida, listado, consulta, eliminación)
- Sistema de votaciones públicas
- Rankings dinámicos por votos
- Procesamiento asíncrono de videos (integrado con worker de Celery)
- Almacenamiento de archivos
- Validaciones y manejo de errores

## Acceso al Servicio

Cuando el sistema completo está ejecutándose (desde la raíz con `docker compose up -d`):

- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc
- **OpenAPI JSON**: http://localhost:8080/api/openapi.json

## Endpoints Principales

### Gestión de Videos (Autenticados)
- `POST /api/videos/upload` - Subir video (201 Created)
- `GET /api/videos` - Listar mis videos (200 OK)
- `GET /api/videos/{id}` - Detalle de video (200 OK)
- `DELETE /api/videos/{id}` - Eliminar video (200 OK)

### Endpoints Públicos
- `GET /api/public/videos` - Listar videos públicos (200 OK)
- `GET /api/public/videos/{id}` - Consultar video público (200 OK)
- `POST /api/public/videos/{id}/vote` - Votar por video (201 Created, requiere auth)
- `GET /api/public/rankings` - Ver rankings (200 OK)

Todos los endpoints están completamente documentados en Swagger UI con ejemplos de request/response.

## Estructura del Proyecto

```
core/
├── app/                   # Código fuente de la aplicación
│   ├── api/               # Endpoints (routers)
│   │   ├── videos.py      # Endpoints de gestión de videos
│   │   └── public.py      # Endpoints públicos
│   ├── schemas/           # Modelos Pydantic (request/response)
│   ├── models/            # Modelos SQLAlchemy (base de datos)
│   ├── services/          # Lógica de negocio
│   ├── exceptions/        # Excepciones personalizadas y handlers
│   ├── core/              # Configuración central y middleware
│   ├── database.py        # Configuración de base de datos
│   └── config.py          # Configuración de la aplicación
├── storage/               # Almacenamiento de archivos
│   ├── uploads/           # Videos originales
│   └── processed/         # Videos procesados
├── tests/                 # Tests unitarios
├── seed_data.py           # Script de datos de prueba
├── Dockerfile             # Imagen Docker de la API
├── requirements.txt       # Dependencias
└── main.py                # Punto de entrada
```

## Desarrollo Local

### Requisitos
- Python 3.12+
- PostgreSQL 15
- Variables de entorno configuradas (ver `.env.example`)

### Configuración

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate      # En Linux/Mac
venv\Scripts\activate         # En Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. Ejecutar la aplicación:
```bash
# Desarrollo (con auto-reload)
fastapi dev main.py

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000
```

La API estará disponible en http://localhost:8000

**Nota:** Para desarrollo local completo del sistema (con worker, RabbitMQ, auth service, etc.), se recomienda usar Docker Compose desde la raíz del proyecto.

## Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app

# Ver reporte HTML de coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Variables de Entorno Principales

Ver `.env.example` para la lista completa de variables configurables.

Principales:
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `APP_NAME`: Nombre de la aplicación
- `DEBUG`: Modo debug (True/False)
- `MAX_UPLOAD_SIZE_MB`: Tamaño máximo de archivos (100MB)
- `ALLOWED_VIDEO_FORMATS`: Formatos permitidos (mp4, avi, mov, mkv)
- `MIN_VIDEO_DURATION_SECONDS`: Duración mínima (20s)
- `MAX_VIDEO_DURATION_SECONDS`: Duración máxima (60s)

## Tecnologías

- **Framework**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Base de Datos**: PostgreSQL 15
- **Validación**: Pydantic
- **Autenticación**: JWT (validado vía middleware)
- **Storage**: Sistema de archivos (con abstracción para futura migración a S3)

## Documentación Adicional

- [README Principal del Proyecto](../README.md)
- [Documentación Entrega 1](../docs/Entrega_1/)
- [Colección de Postman](../collections/)
