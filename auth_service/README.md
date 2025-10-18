# ANB Rising Stars Showcase - Servicio de Autenticación

Servicio de autenticación y gestión de usuarios del sistema ANB Rising Stars Showcase. Maneja registro, login y gestión de tokens JWT.

**Este servicio es parte de un sistema completo. Ver [README principal](../README.md) para instrucciones de despliegue e información general del proyecto.**

## Descripción

API REST desarrollada con FastAPI que proporciona:

- Registro de usuarios (jugadores)
- Autenticación mediante JWT
- Gestión de tokens (access y refresh tokens)
- Validación de credenciales
- Health check del servicio

## Acceso al Servicio

Cuando el sistema completo está ejecutándose (desde la raíz con `docker compose up -d`):

- **Swagger UI**: http://localhost:8080/auth/docs
- **ReDoc**: http://localhost:8080/auth/redoc
- **OpenAPI JSON**: http://localhost:8080/auth/openapi.json

## Endpoints Principales

### Autenticación
- `POST /auth/signup` - Registrar nuevo usuario (201 Created)
- `POST /auth/login` - Iniciar sesión (200 OK)
- `POST /auth/refresh` - Refrescar access token (200 OK)
- `GET /auth/status` - Estado del servicio (200 OK)

Todos los endpoints están completamente documentados en Swagger UI con ejemplos de request/response.

## Estructura del Proyecto

```
auth_service/
├── app/                   # Código fuente de la aplicación
│   ├── api/               # Endpoints (routers)
│   │   └── v1/            # Versión 1 de la API
│   │       └── endpoints/ # Endpoints de auth
│   ├── schemas/           # Modelos Pydantic (request/response)
│   ├── models/            # Modelos SQLAlchemy (base de datos)
│   ├── services/          # Lógica de negocio
│   ├── core/              # Configuración central
│   └── database.py        # Configuración de base de datos
├── Dockerfile             # Imagen Docker del servicio
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
uvicorn main:app --host 0.0.0.0 --port 8001
```

La API estará disponible en http://localhost:8001

**Nota:** Para desarrollo local completo del sistema (con core API, worker, RabbitMQ, etc.), se recomienda usar Docker Compose desde la raíz del proyecto.

## Variables de Entorno Principales

Ver `.env.example` para la lista completa de variables configurables.

Principales:
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `ACCESS_TOKEN_SECRET_KEY`: Clave secreta para tokens de acceso
- `REFRESH_TOKEN_SECRET_KEY`: Clave secreta para tokens de refresco
- `ALGORITHM`: Algoritmo de firma JWT (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiración de access token (15 minutos)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Expiración de refresh token (7 días)

## Tecnologías

- **Framework**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Base de Datos**: PostgreSQL 15
- **Validación**: Pydantic
- **Autenticación**: JWT con python-jose
- **Hashing**: bcrypt para contraseñas

## Documentación Adicional

- [README Principal del Proyecto](../README.md)
- [Documentación Entrega 1](../docs/Entrega_1/)
- [Colección de Postman](../collections/)
