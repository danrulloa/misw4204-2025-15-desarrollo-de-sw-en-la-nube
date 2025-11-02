# ANB Rising Stars Showcase - Contexto Completo del Proyecto

## Información General

**Nombre del Proyecto**: ANB Rising Stars Showcase  
**Curso**: MISW4204 - Desarrollo de Software en la Nube  
**Universidad**: Universidad de los Andes  
**Año**: 2025  
**Equipo**: 
- Daniel Ricardo Ulloa Ospina (d.ulloa@uniandes.edu.co)
- David Cruz Vargas (da.cruz84@uniandes.edu.co)
- Frans Taboada (f.taboada@uniandes.edu.co)
- Nicolás Infante (n.infanter@uniandes.edu.co)

---

## Descripción del Sistema

Sistema completo de gestión de videos y votaciones para jugadores de baloncesto aficionados de la Asociación Nacional de Baloncesto (ANB). Permite a jugadores subir videos de sus habilidades, procesarlos automáticamente y permitir que el público vote por sus favoritos.

### Casos de Uso Principales

1. **Jugadores registrados** suben videos de sus habilidades (20-60 segundos)
2. **Sistema** procesa videos asíncronamente (recorte, normalización, marca de agua)
3. **Público** vota por sus jugadores favoritos
4. **Sistema** genera rankings dinámicos por votos recibidos

---

## Arquitectura del Sistema

### Stack Tecnológico

**Backend y APIs:**
- Python 3.12
- FastAPI (APIs REST)
- Pydantic (validación de datos)
- JWT (autenticación)
- Alembic (migraciones de BD)

**Bases de Datos:**
- PostgreSQL 15 (2 instancias separadas: auth y core)
- SQLAlchemy 2.0+ (ORM asíncrono)
- asyncpg (driver asíncrono PostgreSQL)

**Procesamiento Asíncrono:**
- Celery 5.4 (task queue)
- RabbitMQ 3.10 (message broker)
- FFmpeg (procesamiento de video)

**Infraestructura:**
- Docker y Docker Compose
- Nginx 1.25 (reverse proxy)
- Ubuntu 22.04 (imágenes base)

**Observabilidad:**
- Grafana 11.2.0 (visualización)
- Prometheus v2.54.1 (métricas)
- Loki 2.9.4 (logs)
- Promtail 2.9.4 (colección de logs)
- cAdvisor (métricas de contenedores)
- nginx-exporter, postgres-exporter (exportadores)

### Arquitectura de Microservicios

El sistema está compuesto por **3 servicios principales** más infraestructura:

#### 1. **API Core** (`core/`)
- **Propósito**: API REST principal para gestión de videos y votaciones
- **Puerto**: 8000
- **Base de datos**: `anb_core` (PostgreSQL)
- **Endpoints**: 9 endpoints documentados en OpenAPI/Swagger
- **Características**:
  - Subida de videos con validación
  - Listado y consulta de videos
  - Eliminación de videos
  - Sistema de votación pública
  - Rankings dinámicos
  - Integración con worker Celery

#### 2. **Auth Service** (`auth_service/`)
- **Propósito**: Servicio de autenticación y gestión de usuarios
- **Puerto**: 8000
- **Base de datos**: `anb_auth` (PostgreSQL)
- **Endpoints**: 
  - `POST /auth/api/v1/signup` - Registro de usuarios
  - `POST /auth/api/v1/login` - Inicio de sesión (retorna access + refresh tokens)
  - `POST /auth/api/v1/refresh` - Refrescar access token
  - `GET /auth/api/v1/status` - Estado del servicio
- **Características**:
  - Autenticación JWT con refresh tokens
  - Sesiones de usuario
  - Permisos y grupos
  - Multitenancy

#### 3. **Worker** (`worker/`)
- **Propósito**: Procesamiento asíncrono de videos
- **Herramientas**: Celery + FFmpeg
- **Tareas**:
  - Recorte de video a 30 segundos máximo
  - Normalización a 1280x720 (16:9)
  - Aplicación de marca de agua
  - Concatenación con intro/outro (opcional)
  - Remoción de audio
- **Flujo**:
  1. API envía mensaje a RabbitMQ
  2. Worker consume mensaje
  3. Procesa video con FFmpeg
  4. Actualiza estado en base de datos
  5. Marca video como `processed` o `failed`

### Infraestructura de Soporte

#### **RabbitMQ** (Message Broker)
- **Imagen**: rabbitmq:3.10-management
- **Puerto de gestión**: 15672
- **Credenciales**: rabbit/rabbitpass
- **Arquitectura de Colas**:
  - Exchange `video` (direct)
  - Queue `video_tasks` (principal)
  - Queue `video_dlq` (dead-letter queue)
  - Queues de retry: `video_retry_60s`, `video_retry_2m`, `video_retry_10m`
- **Características**:
  - Colas durables
  - Dead-letter queuing
  - Retries automáticos con backoff
  - Política lazy queues
- **Configuración**: `rabbitmq/definitions.json`

#### **Nginx** (Reverse Proxy)
- **Puerto**: 8080 (externa)
- **Upstreams**:
  - `api_upstream`: anb_api:8000 (API Core)
  - `auth_upstream`: anb-auth-service:8000 (Auth Service)
  - `rmq_mgmt_upstream`: rabbitmq:15672 (RabbitMQ Management)
  - `grafana_upstream`: grafana:3000 (Grafana)
- **Rutas**:
  - `/api/` → API Core (con root_path="/api")
  - `/auth/` → Auth Service
  - `/rabbitmq/` → RabbitMQ Management UI
  - `/grafana/` → Grafana
- **Características**:
  - Proxy inverso
  - Balanceador de carga (keepalive)
  - Configuración para uploads grandes (100MB)
  - Timeouts extendidos para procesamiento

#### **PostgreSQL** (2 instancias)
1. **anb-auth-db**:
   - Base de datos: `anb_auth`
   - Usuario: `anb_user`
   - Tablas: users, sessions, refresh_tokens, groups, permissions, etc.

2. **anb-core-db**:
   - Base de datos: `anb_core`
   - Usuario: `anb_user`
   - Tablas: videos, votes

### Observabilidad

**Stack completo** para monitoreo:
- **Grafana**: Dashboards técnicos con métricas y logs
- **Prometheus**: Recolecta métricas de:
  - FastAPI (instrumentator)
  - Nginx (exporter)
  - PostgreSQL (exporter)
  - RabbitMQ (nativo)
  - cAdvisor (contenedores)
- **Loki**: Agrega logs de todos los servicios
- **Promtail**: Recolecta logs de Docker y archivos
- **Tempo**: Trazado distribuido (opcional)

---

## Modelo de Datos

### Base de Datos: `anb_auth`

#### Tabla: `users`
```sql
- id (PK, Integer)
- email (String, unique, indexado)
- hashed_password (String)
- first_name (String)
- last_name (String)
- country (String, nullable)
- city (String, nullable)
- is_active (Boolean, default true)
- created_at (DateTime, auto)
- tenant_id (Integer, default 0, indexado)
```

#### Tabla: `sessions`
```sql
- id (PK, Integer)
- user_id (FK → users.id)
- token (String, unique)
- expires_at (DateTime)
- created_at (DateTime)
```

#### Tabla: `refresh_tokens`
```sql
- id (PK, Integer)
- session_id (FK → sessions.id)
- token (String, unique)
- expires_at (DateTime)
- created_at (DateTime)
```

#### Tablas de permisos:
- `groups`: id, name, description
- `permissions`: id, name, resource, action
- `user_groups`: user_id, group_id
- `user_permissions`: user_id, permission_id
- `group_permissions`: group_id, permission_id

### Base de Datos: `anb_core`

#### Tabla: `videos`
```sql
- id (PK, UUID)
- user_id (String(64), indexado)  -- ID del usuario propietario
- player_first_name (String, nullable)  -- Desnormalizado del JWT
- player_last_name (String, nullable)
- player_city (String, nullable)
- title (String(255))
- original_filename (String(255))
- original_path (String(500))  -- Ruta relativa a UPLOAD_DIR
- processed_path (String(500), nullable)  -- Ruta relativa a PROCESSED_DIR
- status (Enum: uploaded, processing, processed, failed, indexado)
- duration_seconds (Integer, nullable)
- file_size_mb (Float, nullable)
- processed_at (DateTime, nullable)
- correlation_id (String(100), nullable, indexado)
- created_at (DateTime, auto)
- updated_at (DateTime, auto)
```

**Estados del Video**:
- `uploaded`: Recién subido, esperando procesamiento
- `processing`: En proceso de edición
- `processed`: Listo para votación pública
- `failed`: Error en el procesamiento

#### Tabla: `votes`
```sql
- id (PK, UUID)
- user_id (String(64), indexado)
- video_id (FK → videos.id, CASCADE)
- created_at (DateTime, auto)
- updated_at (DateTime, auto)

Constraint: unique(user_id, video_id)  -- Un usuario solo puede votar una vez por video
Indices: idx_vote_user, idx_vote_video
```

---

## Endpoints de la API

### API Core (`/api/`)

#### Gestión de Videos (Autenticados)
| Método | Endpoint | Descripción | Response |
|--------|----------|-------------|----------|
| POST | `/videos/upload` | Subir video | 201 Created |
| GET | `/videos` | Listar mis videos | 200 OK |
| GET | `/videos/{id}` | Detalle de video | 200 OK |
| DELETE | `/videos/{id}` | Eliminar video | 200 OK |

#### Endpoints Públicos
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/public/videos` | Listar videos públicos | No |
| GET | `/public/videos/{id}` | Consultar video público | No |
| POST | `/public/videos/{id}/vote` | Votar por video | Sí |
| GET | `/public/rankings` | Ver rankings | No |

#### Health Checks
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check de la API |
| GET | `/` | Info básica |

**Swagger UI**: http://localhost:8080/api/docs

### Auth Service (`/auth/`)

| Método | Endpoint | Descripción | Response |
|--------|----------|-------------|----------|
| POST | `/api/v1/signup` | Registrar usuario | 201 Created |
| POST | `/api/v1/login` | Iniciar sesión | 200 OK (access + refresh tokens) |
| POST | `/api/v1/refresh` | Refrescar access token | 200 OK |
| GET | `/api/v1/status` | Estado del servicio | 200 OK |

**Swagger UI**: http://localhost:8080/auth/docs

---

## Flujos de Datos Principales

### Flujo 1: Subida y Procesamiento de Video

1. **Cliente → API Core**: `POST /api/videos/upload` con archivo de video + metadata
2. **API Core valida**:
   - Formato: mp4, avi, mov
   - Tamaño: máx 100 MB
   - Duración: 20-60 segundos
   - Token JWT válido
3. **API Core guarda**:
   - Video en storage local
   - Registro en BD con status="uploaded"
   - Desnormaliza datos del jugador del JWT
4. **API Core → RabbitMQ**: Publica mensaje a cola `video_tasks` con (video_id, input_path, correlation_id)
5. **Worker consume** mensaje y procesa:
   - Recorta a 30s máximo
   - Normaliza a 1280x720
   - Aplica marca de agua
   - Concatena intro/outro si existen
   - Remueve audio
6. **Worker actualiza BD**: status="processed", processed_path, processed_at
7. **Respuesta al cliente**: Video disponible para votación

### Flujo 2: Votación

1. **Cliente → API Core**: `POST /api/public/videos/{id}/vote` con token JWT
2. **API Core valida**:
   - Video existe y está procesado
   - Usuario no ha votado antes (unique constraint)
   - Token JWT válido
3. **API Core crea** registro en tabla `votes`
4. **Respuesta**: Confirmación de voto

### Flujo 3: Ranking

1. **Cliente → API Core**: `GET /api/public/rankings?city=Bogotá&limit=10`
2. **API Core consulta BD**:
   ```sql
   SELECT user_id, player_first_name, player_last_name, player_city, 
          COUNT(votes.id) as total_votes
   FROM videos
   JOIN votes ON votes.video_id = videos.id
   WHERE videos.status = 'processed'
   GROUP BY user_id, player_first_name, player_last_name, player_city
   ORDER BY total_votes DESC
   LIMIT 10
   ```
3. **Respuesta**: Lista ordenada por votos

### Flujo 4: Autenticación

1. **Cliente → Auth Service**: `POST /auth/api/v1/login` con credenciales
2. **Auth Service valida**:
   - Email y password correctos
   - Usuario activo
3. **Auth Service genera**:
   - Access token JWT (expira en X minutos)
   - Refresh token (almacenado en BD)
4. **Respuesta**: `{access_token, refresh_token, token_type: "bearer", expires_in}`
5. **Cliente usa** access_token en header `Authorization: Bearer <token>`

---

## Almacenamiento de Archivos

### Local (Desarrollo)
- **Directorio de uploads**: `core/storage/uploads/`
- **Directorio de procesados**: `core/storage/processed/`
- **Estructura**: `uploads/YYYY/MM/DD/`
- **Volúmenes Docker**: Montados en containers

### S3 (Producción - Pendiente)
- **Bucket**: `anb-basketball-bucket`
- **Región**: us-east-1
- **Driver**: boto3
- **Configuración**: En `core/app/config.py`

**Configuración de STORAGE_BACKEND**:
- `"local"`: Almacenamiento en filesystem
- `"s3"`: Almacenamiento en S3

---

## Procesamiento de Videos

### Pipeline FFmpeg

El worker ejecuta el siguiente pipeline:

1. **Entradas**:
   - Video principal (input_path)
   - Intro/Outro (ANB_INOUT_PATH, opcional)
   - Watermark (ANB_WATERMARK_PATH)

2. **Procesamiento**:
   ```
   - Recorte: trim=0:30 (30s máximo)
   - Escalado: 1280x720 manteniendo aspect ratio
   - Pad: relleno a 1280x720 (centrado)
   - Watermark: overlay en esquina superior derecha
   - Concat: intro + main + outro
   - Códec: libx264, preset=veryfast, crf=23
   - Audio: removido (-an)
   ```

3. **Salida**: MP4 en processed_path

### Manejo de Errores

- **Retries**: 2 intentos con countdown 30s
- **DLQ**: Fallos después de 3 intentos van a `video_dlq`
- **Logging**: Logs detallados en cada paso
- **Base de datos**: Status actualizado a "failed" si falla definitivamente

---

## Seguridad

### Autenticación JWT

- **Algoritmo**: HS256
- **Campos del token**:
  - `sub`: username
  - `user_id`: ID del usuario
  - `tenant_id`: ID del tenant
  - `permissions`: Lista de permisos
  - `first_name`, `last_name`, `city`: Datos del jugador
  - `exp`, `iat`: Timestamps
- **Verificación**: En `AuthMiddleware` (core y auth_service)

### Variables de Entorno Críticas

```bash
# JWT
ACCESS_TOKEN_SECRET_KEY=<secreto>
REFRESH_TOKEN_SECRET_KEY=<secreto>
ALGORITHM=HS256
TOKEN_EXPIRE=30  # minutos
REFRESH_TOKEN_EXPIRE=1440  # minutos

# Issuer/Audience
AUTH_ISSUER=anb-auth
AUTH_AUDIENCE=anb-api

# RabbitMQ
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass

# Base de datos
POSTGRES_DB=anb_auth
POSTGRES_CORE_DB=anb_core
POSTGRES_USER=anb_user
POSTGRES_PASSWORD=anb_pass

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

---

## Testing

### Cobertura
- **Cobertura objetivo**: >80%
- **Herramienta**: pytest-cov
- **Comandos**:
  ```bash
  cd core && pytest --cov=app tests/
  cd auth_service && pytest --cov=app tests/
  ```

### Colección Postman
- **Ubicación**: `collections/ANB_Basketball_API.postman_collection.json`
- **Endpoints**: 14 endpoints con tests automatizados
- **Variables**: Auto-guardado de tokens y IDs
- **Ejecución**:
  ```bash
  newman run collections/ANB_Basketball_API.postman_collection.json \
    -e collections/ANB_Basketball_API.postman_environment.json
  ```

### Pruebas de Carga (k6)
- **Scripts**: `K6/*.js`
- **Escenarios**: Sanidad, escalamiento, sostenida
- **Métricas**: Latencia p95, throughput, errores

---

## Despliegue

### Local (Docker Compose)
```bash
# Levantar servicios
docker compose up -d

# Verificar
docker compose ps

# Logs
docker compose logs -f anb_api

# Cargar datos de prueba
docker compose exec anb_api python seed_data.py

# Detener
docker compose down -v
```

### AWS (Terraform)
- **Infraestructura**: `infra/main.tf`
- **Instancias**: 6 EC2 (t3.small)
- **Redes**: VPC con security groups
- **Servicios**: Docker Compose multihost con perfiles
- **Balanceador**: ALB público
- **Estado**: Ver `docs/Entrega_2/README.md`

**Componentes desplegados**:
1. Web Server: Nginx
2. Core Services: API + Auth
3. Worker: Celery
4. Database: PostgreSQL (containers)
5. MQ: RabbitMQ
6. Observability: Prometheus + Grafana + Loki

---

## Observabilidad

### Grafana
- **URL**: http://localhost:8080/grafana/
- **Credenciales**: admin/admin
- **Dashboards**: Técnico con métricas de servicios

### Prometheus
- **Puerto**: 9090
- **Targets**: APIs, exporters, RabbitMQ

### Métricas Principales
- Request rate, latency (FastAPI)
- Queue depth, messages (RabbitMQ)
- Connections, queries (PostgreSQL)
- CPU, memory (cAdvisor)

### Logs (Loki)
- Logs agregados de todos los servicios
- Niveles: INFO, WARNING, ERROR
- Búsqueda y filtrado en Grafana

---

## Estado del Proyecto

### Entrega 1 ✅
- API REST completa
- Procesamiento asíncrono
- Observabilidad
- Testing >80%
- Documentación

### Entrega 2 ✅
- Despliegue AWS con Terraform
- 6 instancias EC2
- Pruebas de carga
- SonarQube

### Pendientes
- Migración a RDS (PostgreSQL managed)
- NFS Server dedicado
- S3 para almacenamiento
- CI/CD pipeline
- Autoscaling

---

## Archivos Clave

### Configuración
- `compose.yaml`: Orquestación local
- `docker-compose.multihost.yml`: Despliegue AWS
- `nginx/nginx.conf`: Configuración reverse proxy
- `rabbitmq/definitions.json`: Topología de colas
- `infra/main.tf`: Infraestructura AWS
- `.env`: Variables de entorno (no en repo)

### Documentación
- `README.md`: Inicio rápido
- `CONTEXT.md`: Este archivo
- `docs/Entrega_1/README.md`: Entrega 1
- `docs/Entrega_2/README.md`: Entrega 2
- Wiki de GitHub: Documentación detallada

### Código Principal
- `core/main.py`: Entrypoint API Core
- `core/app/api/videos.py`: Endpoints de videos
- `core/app/api/public.py`: Endpoints públicos
- `core/app/core/auth_middleware.py`: Middleware JWT
- `auth_service/app/main.py`: Entrypoint Auth Service
- `worker/tasks/process_video.py`: Tarea de procesamiento

---

## Comandos Útiles

### Desarrollo
```bash
# Reconstruir
docker compose up -d --build --force-recreate

# Logs en tiempo real
docker compose logs -f anb_api worker

# Shell en container
docker compose exec anb_api bash

# Reiniciar servicio
docker compose restart worker

# Ver colas RabbitMQ
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

### Testing
```bash
# Unit tests con cobertura
cd core && pytest --cov=app tests/
cd auth_service && pytest --cov=app tests/

# Postman
newman run collections/ANB_Basketball_API.postman_collection.json \
  -e collections/ANB_Basketball_API.postman_environment.json
```

### Observabilidad
```bash
# RabbitMQ UI
http://localhost:8080/rabbitmq

# Grafana
http://localhost:8080/grafana/

# Prometheus
http://localhost:9090

# Metrics endpoint
curl http://localhost:8080/api/metrics
```

---

## Decisiones de Diseño

### Arquitectura de Microservicios
**Razón**: Separación de responsabilidades, escalabilidad independiente, deploy independiente

### Dos Bases de Datos Separadas
**Razón**: Separar datos de negocio (videos) de autenticación, permitir escalado independiente

### RabbitMQ vs Redis
**Razón**: Dead-letter queuing nativo, lazy queues, management UI, mejor para tareas largas

### JWT en lugar de Sessions
**Razón**: Stateless, escalable, funciona en microservicios, refresh tokens para seguridad

### Desnormalización de Datos del Jugador
**Razón**: Queries públicas más rápidas, evitar joins, datos desde JWT

### Volúmenes Docker Compartidos
**Razón**: Simplicidad en desarrollo, migración a S3/NFS pendiente

---

## Errores Comunes y Soluciones

### Puerto en uso
```bash
# Ver qué está usando el puerto
lsof -i :8080

# Cambiar puerto en compose.yaml
nginx:
  ports: "8081:80"
```

### Videos no se procesan
```bash
# Verificar worker corriendo
docker compose ps worker

# Ver logs del worker
docker compose logs -f worker

# Verificar colas RabbitMQ
docker compose exec rabbitmq rabbitmqctl list_queues
```

### Error de autenticación
- Verificar `ACCESS_TOKEN_SECRET_KEY` en `.env`
- Verificar configuración JWT en ambos servicios
- Verificar middleware activado

### Base de datos bloqueada
```bash
# Recrear volúmenes
docker compose down -v
docker compose up -d
```

---

## Referencias

- [README Principal](./README.md)
- [Wiki del Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki)
- [Arquitectura RabbitMQ](./rabbitmq/ARQUITECTURA_RABBITMQ.md)
- [Entrega 1](./docs/Entrega_1/README.md)
- [Entrega 2](./docs/Entrega_2/README.md)

---

---

## Performance y Optimizaciones

### Línea Base de Performance

**Objetivo**: Lograr **<1s** de tiempo de respuesta para upload de videos de **100MB**.

**Métricas actuales** (Branch: develop, fecha: 2025-11-01):
- **9MB (1 VU)**: 338ms ✅
- **100MB (1 VU)**: 7.81s ❌ (objetivo: <1s)
- **100MB (5 VUs)**: p95=38.06s ❌ (crítico)

**Análisis**:
- Bajo carga simple: Performance aceptable para archivos pequeños
- Bajo concurrencia: `waiting time` (30.78s) >> `sending time` (7.9s)
- Indica cuello de botella en base de datos o RabbitMQ

**Herramientas de testing**:
- k6 scripts en `/K6/*.js`
- Pruebas de sanidad y escalamiento
- Métricas: latencia p95, throughput, errores

### Plan de Optimizaciones

**Documentación completa**: Ver `PLAN_OPTIMIZACIONES.md`

**Optimizaciones completadas**:
- ✅ RabbitMQ healthcheck fix (timeout: 30s, start_period: 90s)
- ✅ Nginx configuración para local vs cloud
- ✅ Storage backend local para desarrollo
- ✅ RABBITMQ_URL configuration

**Optimizaciones pendientes** (orden recomendado):
1. Reducción de commits a base de datos (3→1 con flush)
2. Pool de conexiones asíncrono para RabbitMQ (aio-pika)
3. Optimización de pool PostgreSQL
4. Investigación de bloqueos en base de datos
5. Async file writing con streaming (chunks)
6. Desactivar buffering en Nginx para uploads
7. Escalamiento horizontal de workers

**Lecciones aprendidas**:
- ✅ Healthchecks adecuados son críticos para infraestructura
- ❌ `aiofiles` sin streaming empeora performance
- ❌ Concurrencia es el problema real, no velocidad individual
- ⚠️ Medir primero, optimizar después

---

## Configuración Local vs Cloud

**Documentación completa**: Ver `SETUP_LOCAL_VS_CLOUD.md`

**Ambiente Local**:
- Storage: `local` en filesystem
- Upstreams Nginx: nombres de servicios Docker
- RabbitMQ healthcheck: timeout 30s, start_period 90s

**Ambiente Cloud** (AWS):
- Storage: S3 con credenciales IAM
- Upstreams Nginx: IPs de instancias EC2
- RabbitMQ: configuración estándar

**Variables críticas**:
- `STORAGE_BACKEND`: "local" vs "s3"
- `RABBITMQ_URL`: conexión RabbitMQ
- Nginx upstreams: servicios vs IPs

---

## Documentación Adicional

- `README.md`: Inicio rápido y acceso a servicios
- `CONTEXT.md`: Este archivo (contexto completo)
- `BASELINE.md`: Línea base de performance
- `PLAN_OPTIMIZACIONES.md`: Plan detallado de optimizaciones
- `SETUP_LOCAL_VS_CLOUD.md`: Configuración local vs cloud
- `docs/Entrega_1/README.md`: Documentación Entrega 1
- `docs/Entrega_2/README.md`: Documentación Entrega 2
- Wiki de GitHub: Documentación detallada

---

**Última actualización**: 2025-11-01
**Versión del documento**: 2.0.0

