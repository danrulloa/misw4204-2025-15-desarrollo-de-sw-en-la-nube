# ANB Rising Stars Showcase - Sistema de Procesamiento de Videos

Sistema completo para la gestión de videos y votaciones de jugadores de baloncesto de la Asociación Nacional de Baloncesto (ANB). El sistema permite a jugadores aficionados subir videos de sus habilidades, procesarlos automáticamente y permitir que el público vote por sus favoritos.

**Curso:** MISW4204 - Desarrollo de Software en la Nube
**Universidad:** Universidad de los Andes
**Año:** 2025

---

## Documentación Completa

**Para documentación detallada del proyecto, arquitectura, guías de despliegue, análisis de capacidad y más, consulta la [Wiki del Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki).**

---

## Equipo

| Nombre | Correo Institucional |
|--------|---------------------|
| Daniel Ricardo Ulloa Ospina | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |

---

## Descripción del Sistema

El sistema ANB Rising Stars Showcase está compuesto por una arquitectura de microservicios orquestados con Docker Compose:

- **API Principal (Core)**: API REST para gestión de videos y votaciones
- **Servicio de Autenticación**: Manejo de usuarios, sesiones y tokens JWT con refresh tokens
- **Worker**: Procesamiento asíncrono de videos con Celery y FFmpeg
- **RabbitMQ**: Broker de mensajería para tareas asíncronas con colas durables y dead-letter queuing
- **PostgreSQL**: Dos instancias de bases de datos (auth y core)
- **Nginx**: Proxy inverso y balanceador de carga
- **Stack de Observabilidad**: Grafana, Prometheus, Loki, Promtail para monitoreo completo

### Características Principales

- API RESTful con 9 endpoints documentados en OpenAPI/Swagger
- Autenticación y autorización con JWT
- Procesamiento asíncrono de videos (recorte, normalización, marca de agua)
- Sistema de votación pública con rankings dinámicos
- Observabilidad completa con métricas, logs y traces distribuidos
- Pruebas unitarias con cobertura superior al 80%
- Colección Postman con tests automatizados

---

## Inicio Rápido

### Prerrequisitos

- Docker Desktop (o Docker Engine) instalado y corriendo
- Docker Compose

### Levantar el Sistema

```bash
# Clonar el repositorio
git clone https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube.git
cd misw4204-2025-15-desarrollo-de-sw-en-la-nube

# Levantar todos los servicios
docker compose up -d

# Verificar estado de los servicios
docker compose ps

# Cargar datos de prueba (opcional)
docker compose exec anb_api python seed_data.py
```

### Detener el Sistema

```bash
docker compose down

# Para eliminar también los volúmenes (base de datos)
docker compose down -v
```

---

## Acceso a Servicios

Una vez levantados los servicios, puedes acceder a:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Swagger API Principal | http://localhost:8080/api/docs | - |
| Swagger Autenticación | http://localhost:8080/auth/docs | - |
| RabbitMQ Management | http://localhost:15672 | rabbit / rabbitpass |
| Grafana | http://localhost:8080/grafana/ | admin / admin |

Para más detalles sobre cómo usar estos servicios, consulta la [Wiki - Cómo Iniciar](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Cómo-Iniciar).

---

## Estructura del Proyecto

```
.
├── core/                  # API principal (FastAPI)
│   ├── app/               # Código de la aplicación
│   ├── storage/           # Almacenamiento de videos
│   ├── tests/             # Tests unitarios
│   └── README.md          # Documentación de desarrollo local
├── auth_service/          # Servicio de autenticación
│   ├── app/               # Código de autenticación
│   ├── tests/             # Tests unitarios
│   └── README.md          # Documentación de desarrollo local
├── worker/                # Worker de procesamiento (Celery)
│   ├── tasks/             # Tareas de Celery
│   └── README.md          # Documentación de desarrollo local
├── nginx/                 # Configuración de Nginx
│   └── nginx.conf         # Configuración del proxy inverso
├── rabbitmq/              # Configuración de RabbitMQ
│   ├── definitions.json   # Definición de colas/exchanges
│   └── ARQUITECTURA_RABBITMQ.md  # Documentación técnica
├── observability/         # Stack de observabilidad
│   ├── grafana/           # Configuración de Grafana
│   ├── prometheus/        # Configuración de Prometheus
│   ├── loki/              # Configuración de Loki
│   ├── promtail/          # Configuración de Promtail
│   └── tempo/             # Configuración de Tempo
├── collections/           # Colección de Postman
│   ├── ANB_Basketball_API.postman_collection.json
│   ├── ANB_Basketball_API.postman_environment.json
│   └── README.md          # Guía de uso de Postman
├── docs/                  # Documentación del proyecto
│   └── Entrega_1/         # Documentación Entrega 1
├── compose.yaml           # Orquestación de servicios
└── README.md              # Este archivo
```

---

## Stack Tecnológico

### Backend y APIs
- Python 3.12
- FastAPI
- Pydantic (validación)
- JWT (autenticación)

### Bases de Datos
- PostgreSQL 15 (2 instancias)

### Procesamiento Asíncrono
- Celery (task queue)
- RabbitMQ 3.10 (message broker)
- FFmpeg (procesamiento de video)

### Infraestructura
- Nginx 1.25 (reverse proxy)
- Docker y Docker Compose
- Ubuntu (base images)

### Observabilidad
- Grafana (visualización)
- Prometheus (métricas)
- Loki (logs)
- Promtail (log collection)
- Exportadores: nginx-exporter, pg-exporter, cAdvisor

---

## Documentación Adicional

### Wiki del Proyecto
La documentación completa se encuentra en la [Wiki de GitHub](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki):

- [Cómo Iniciar](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Cómo-Iniciar) - Guía de instalación y configuración
- [Observabilidad](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Observabilidad) - Stack de monitoreo y logs
- [Testing](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Testing) - Pruebas unitarias y Postman
- [Arquitectura](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura) - Diagramas y decisiones de diseño
- [Pruebas de Carga](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-de-Carga) - Análisis de capacidad
- [Entrega 1](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-1) - Resumen de la primera entrega

### READMEs de Servicios
- [core/README.md](core/README.md) - API Principal (desarrollo local)
- [auth_service/README.md](auth_service/README.md) - Servicio de Autenticación (desarrollo local)
- [worker/README.md](worker/README.md) - Worker de Procesamiento (desarrollo local)
- [collections/README.md](collections/README.md) - Guía de Colección Postman
- [rabbitmq/ARQUITECTURA_RABBITMQ.md](rabbitmq/ARQUITECTURA_RABBITMQ.md) - Arquitectura de RabbitMQ

### Documentación de Entregas
- [docs/Entrega_1/README.md](docs/Entrega_1/README.md) - Documentación Entrega 1

---

## Comandos Útiles

### Ver logs de servicios

```bash
docker compose logs -f anb_api          # API principal
docker compose logs -f anb-auth-service # Servicio de autenticación
docker compose logs -f worker           # Worker de procesamiento
docker compose logs -f rabbitmq         # RabbitMQ
```

### Reiniciar servicios

```bash
docker compose restart anb_api
docker compose restart worker
```

### Ejecutar comandos en contenedores

```bash
# Shell en el contenedor de la API
docker compose exec anb_api bash

# Cargar datos de prueba
docker compose exec anb_api python seed_data.py

# Ver colas de RabbitMQ
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

### Reconstruir servicios

```bash
# Reconstruir con cambios en el código
docker compose up -d --build --force-recreate

# Limpiar y reconstruir todo
docker compose down -v
docker compose up -d --build
```

---

## Troubleshooting

### Los servicios no levantan

```bash
# Ver logs detallados
docker compose logs

# Reconstruir desde cero
docker compose down -v
docker compose up -d --build
```

### Puerto en uso

Si el puerto 8080 está en uso, edita `compose.yaml`:

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