# ANB Rising Stars Showcase - Sistema de Procesamiento de Videos

Sistema completo para la gestión de videos y votaciones de jugadores de baloncesto de la Asociación Nacional de Baloncesto (ANB). El sistema permite a jugadores aficionados subir videos de sus habilidades, procesarlos automáticamente y permitir que el público vote por sus favoritos.

## Equipo

| Nombre | Contacto |
|---|---|
| Daniel Ricardo Ulloa | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |

## Descripción del Sistema

El sistema está compuesto por varios servicios orquestados con Docker:

- **API Principal (Core)**: API REST para gestión de videos y votaciones
- **Servicio de Autenticación**: Manejo de usuarios y sesiones JWT
- **Worker**: Procesamiento asíncrono de videos con Celery
- **RabbitMQ**: Broker de mensajería para tareas asíncronas
- **PostgreSQL**: Dos bases de datos (auth y core)
- **Nginx**: Proxy inverso y balanceador de carga

## Requisitos

- Docker Desktop (o Docker Engine) instalado y corriendo
- Docker Compose v2 (comando `docker compose`)

## Inicio Rápido

### Levantar todos los servicios

En PowerShell ejecuta:

```powershell
docker compose up -d
```

Esto levantará automáticamente todos los servicios necesarios. Para detenerlos y remover los contenedores:

```powershell
docker compose down
```

### Forzar reconstrucción (si hay cambios en el código)

```powershell
docker compose pull
docker compose up -d --build --force-recreate --remove-orphans
```

## Acceso a Servicios

Una vez levantados los servicios, puedes acceder a:

### Documentación API

- **Swagger API Principal**: http://localhost:8080/api/docs
- **ReDoc API Principal**: http://localhost:8080/api/redoc
- **Swagger Autenticación**: http://localhost:8080/auth/docs
- **ReDoc Autenticación**: http://localhost:8080/auth/redoc

### Herramientas de Monitoreo

- **RabbitMQ Management**: http://localhost:15672 (usuario: `rabbit`, contraseña: `rabbitpass`)

### Endpoints de la API

Todos los endpoints están documentados en Swagger UI. Principales rutas:

**Autenticación:**
- `POST /auth/api/v1/signup` - Registro de usuarios (201 Created)
- `POST /auth/api/v1/login` - Inicio de sesión (200 OK)
- `POST /auth/api/v1/refresh` - Refrescar token (200 OK)

**Gestión de Videos (requieren autenticación):**
- `POST /api/videos/upload` - Subir video (201 Created)
- `GET /api/videos` - Listar mis videos (200 OK)
- `GET /api/videos/{id}` - Detalle de video (200 OK)
- `DELETE /api/videos/{id}` - Eliminar video (200 OK)

**Endpoints Públicos:**
- `GET /api/public/videos` - Listar videos públicos (200 OK)
- `GET /api/public/videos/{id}` - Consultar video público (200 OK)
- `POST /api/public/videos/{id}/vote` - Votar por video (201 Created)
- `GET /api/public/rankings` - Ver rankings (200 OK)

## Carga de Datos de Prueba

Para facilitar las pruebas, puedes cargar datos de ejemplo (5 videos y 21 votos):

```bash
docker compose exec anb_api python seed_data.py
```

Este script crea:
- 5 videos de muestra en diferentes estados (uploaded, processing, processed, failed)
- 21 votos distribuidos entre los videos
- Usuarios de prueba con datos completos

## Colección de Postman

El proyecto incluye una colección completa de Postman para probar todos los endpoints.

### Importar la colección

1. Abre Postman
2. Click en **Import**
3. Selecciona los archivos:
   - `collections/ANB_Basketball_API.postman_collection.json`
   - `collections/ANB_Basketball_API.postman_environment.json`
4. Selecciona el environment "ANB Basketball API - Local Environment" en el dropdown superior derecho

### Ejecutar con Newman (CLI)

```bash
npm install -g newman
newman run collections/ANB_Basketball_API.postman_collection.json \
  -e collections/ANB_Basketball_API.postman_environment.json
```

La colección incluye:
- 14 endpoints con tests automatizados
- Validación de códigos HTTP correctos
- Scripts que guardan automáticamente tokens y IDs para facilitar el flujo de pruebas

## Pruebas Unitarias y Coverage

El proyecto incluye pruebas unitarias para los servicios core y auth con coverage configurado.

### Requisitos previos

- Python 3.12+ (testeado con Python 3.13)
- pip actualizado

### Configuración inicial del entorno virtual

**Crear entorno virtual (solo la primera vez):**

```bash
# Desde la raíz del proyecto
python -m venv venv
```

**Activar entorno virtual:**

```bash
# Windows PowerShell/CMD:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

Verás `(venv)` al inicio de tu línea de comando cuando esté activo.

### Ejecutar pruebas del servicio Core

```bash
# 1. Ir al directorio core
cd core

# 2. Instalar dependencias (primera vez o si hay cambios)
pip install -r requirements.txt

# 3. Ejecutar pruebas con coverage
pytest

# 4. Ver reporte HTML detallado
start htmlcov\index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Ejecutar pruebas del servicio Auth

```bash
# 1. Ir al directorio auth_service (desde raíz)
cd auth_service

# 2. Instalar dependencias (primera vez o si hay cambios)
pip install -r requirements.txt

# 3. Ejecutar pruebas con coverage
pytest

# 4. Ver reporte HTML detallado
start htmlcov\index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Configuración de Coverage

Ambos servicios están configurados para:
- **Coverage mínimo**: 80%
- **Reporte en terminal**: Muestra líneas faltantes con `--cov-report=term-missing`
- **Reporte HTML**: Visualización detallada por archivo en `htmlcov/`

La configuración se encuentra en:
- [core/pytest.ini](core/pytest.ini)
- [auth_service/pytest.ini](auth_service/pytest.ini)

### Pruebas disponibles

**Servicio Core** ([core/tests/](core/tests/)):
- `test_config.py` - Configuración de la aplicación
- `test_exceptions.py` - Manejo de excepciones
- `test_schemas_video.py` - Validación de schemas de video
- `test_schemas_vote.py` - Validación de schemas de voto
- `test_api_endpoints.py` - Endpoints de la API

**Servicio Auth** ([auth_service/tests/](auth_service/tests/)):
- `test_status.py` - Health check del servicio

### Notas importantes para Windows

Algunos paquetes no son compatibles con Windows y están comentados en `requirements.txt`:

- **`psycopg2-binary`**: No compila en Windows. Se usa `asyncpg` en su lugar.
- **`uvloop`**: Solo disponible en Linux/Mac. No es necesario para desarrollo local.

Estos paquetes **sí funcionan en Docker** porque los contenedores usan Linux.

### Desactivar entorno virtual

Cuando termines de trabajar:

```bash
deactivate
```

## Arquitectura

### Componentes Principales

El sistema utiliza Nginx como proxy inverso que recibe las peticiones y las distribuye entre los servicios:

- **Nginx** (puerto 8080): Proxy inverso que protege la API de conexiones lentas y bufferiza uploads
- **API Principal** (FastAPI): Gestión de videos, votaciones y lógica de negocio
- **Servicio de Autenticación** (FastAPI): Manejo de usuarios, sesiones y tokens JWT
- **RabbitMQ**: Broker de mensajería con colas durables y dead-letter queuing
- **Worker** (Celery): Procesamiento asíncrono de videos
- **PostgreSQL** (2 instancias): Bases de datos separadas para auth y core

### Procesamiento Asíncrono

```
Usuario sube video → API guarda archivo → Encola tarea en RabbitMQ
                                              ↓
                        Worker procesa video ← RabbitMQ entrega tarea
                                              ↓
                        - Recorta a 30 segundos
                        - Ajusta a 720p (16:9)
                        - Agrega marca de agua ANB
                        - Actualiza estado en BD
```

### RabbitMQ - Colas y Reintentos

El sistema usa RabbitMQ con una arquitectura de colas para manejo de reintentos y dead-letter:

- **`video_tasks`**: Cola principal de procesamiento
- **`video_retry_60s`**: Cola de reintento con TTL de 60 segundos
- **`video_dlq`**: Dead Letter Queue para mensajes que fallaron definitivamente

Para detalles técnicos sobre la arquitectura de RabbitMQ (exchanges, bindings, DLX, patrones de retry), consulta:
- [Documentación de Arquitectura RabbitMQ](docs/ARQUITECTURA_RABBITMQ.md)

## Comandos Útiles

### Ver logs de un servicio específico

```bash
docker compose logs -f anb_api          # API principal
docker compose logs -f anb-auth-service # Servicio de auth
docker compose logs -f worker           # Worker de procesamiento
docker compose logs -f rabbitmq         # RabbitMQ
```

### Reiniciar un servicio específico

```bash
docker compose restart anb_api
docker compose restart worker
```

### Ejecutar comandos dentro de un contenedor

```bash
# Shell en el contenedor de la API
docker compose exec anb_api bash

# Shell en el contenedor del worker
docker compose exec worker bash

# Ejecutar script de datos de prueba
docker compose exec anb_api python seed_data.py
```

### Ver estado de todos los servicios

```bash
docker compose ps
```

### Ver colas de RabbitMQ

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

## Estructura del Proyecto

```
.
├── core/                  # API principal (FastAPI)
│   ├── app/               # Código de la aplicación
│   ├── storage/           # Almacenamiento de videos
│   ├── tests/             # Tests unitarios
│   ├── Dockerfile
│   └── requirements.txt
├── auth_service/          # Servicio de autenticación
│   ├── app/               # Código de autenticación
│   ├── Dockerfile
│   └── requirements.txt
├── worker/                # Worker de procesamiento (Celery)
│   ├── tasks/             # Tareas de Celery
│   ├── Dockerfile
│   └── requirements.txt
├── nginx/                 # Configuración de Nginx
│   └── nginx.conf
├── rabbitmq/              # Configuración de RabbitMQ
│   └── definitions.json   # Definición de colas/exchanges
├── collections/           # Colección de Postman
│   ├── ANB_Basketball_API.postman_collection.json
│   └── ANB_Basketball_API.postman_environment.json
├── docs/                  # Documentación del proyecto
│   ├── Entrega_1/         # Documentación Entrega 1
│   │   ├── modelo_datos_erd.png
│   │   └── ...
│   └── ARQUITECTURA_RABBITMQ.md
├── compose.yaml           # Orquestación de servicios
└── README.md              # Este archivo
```

## Documentación

La documentación completa del proyecto se encuentra en:
- **Entrega 1**: [docs/Entrega_1/](docs/Entrega_1/)
  - Modelo de datos (ERD)
  - Documentación de API (Postman)
  - Diagramas de arquitectura
  - Validación de códigos HTTP

## Desarrollo Local

Cada servicio puede ejecutarse localmente para desarrollo. Ver README específicos:
- [core/README.md](core/README.md) - API Principal
- [auth_service/README.md](auth_service/README.md) - Servicio de Autenticación
- [worker/README.md](worker/README.md) - Worker de procesamiento

## Tecnologías Utilizadas

- **Backend**: Python 3.12, FastAPI
- **Base de Datos**: PostgreSQL 15
- **Message Broker**: RabbitMQ 3.10
- **Task Queue**: Celery
- **Proxy**: Nginx 1.25
- **Contenedores**: Docker, Docker Compose
- **Procesamiento de Video**: FFmpeg
- **Autenticación**: JWT (JSON Web Tokens)

## Troubleshooting

### Los servicios no levantan

```bash
# Ver logs detallados
docker compose logs

# Reconstruir desde cero
docker compose down -v
docker compose up -d --build
```

### Error de puerto en uso

Si el puerto 8080 está en uso, puedes cambiar el puerto en `compose.yaml`:

```yaml
nginx:
  ports:
    - "8081:80"  # Cambiar 8080 por otro puerto
```

### Videos no se procesan

1. Verificar que el worker está corriendo:
   ```bash
   docker compose ps worker
   ```

2. Ver logs del worker:
   ```bash
   docker compose logs -f worker
   ```

3. Verificar colas de RabbitMQ en http://localhost:15672

## Soporte

Para reportar problemas o solicitar ayuda, contactar a cualquier miembro del equipo.

## Licencia

Este proyecto es parte del curso MISW4204 - Desarrollo de Software en la Nube, Universidad de los Andes.
