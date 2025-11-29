# ANB Rising Stars Showcase

**Proyecto Académico** - Sistema de Procesamiento de Videos y Votaciones

**Curso:** MISW4204 - Desarrollo de Software en la Nube  
**Universidad:** Universidad de los Andes  
**Año:** 2025  
**Equipo:** 

| Nombre | Correo Institucional |
|--------|---------------------|
| Daniel Ricardo Ulloa Ospina | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |

---

## Descripción del Proyecto

ANB Rising Stars Showcase es un sistema completo para la gestión de videos y votaciones de jugadores de baloncesto de la Asociación Nacional de Baloncesto (ANB). El sistema permite a jugadores aficionados subir videos de sus habilidades, procesarlos automáticamente y permitir que el público vote por sus favoritos.

### Características Principales

- API RESTful con 9 endpoints documentados en OpenAPI/Swagger
- Autenticación y autorización con JWT y refresh tokens
- Procesamiento asíncrono de videos (redimensionamiento, conversión, marca de agua)
- Sistema de votación pública con rankings dinámicos
- Observabilidad completa con métricas, logs y traces distribuidos
- Pruebas unitarias con cobertura superior al 80%
- Colección Postman con tests automatizados

---

## Versiones del Proyecto

Este proyecto ha evolucionado a lo largo de **4 entregas académicas**, cada una representando una versión diferente del sistema con mejoras en escalabilidad, infraestructura y servicios gestionados.

### Resumen Comparativo

| Aspecto | **Entrega 1** | **Entrega 2** | **Entrega 3** | **Entrega 4** | **Entrega 5** |
|---------|---------------|---------------|---------------|---------------|---------------|
| **Ambiente** | Docker Compose Local | AWS EC2 (6 instancias) | AWS con servicios gestionados | AWS con servicios gestionados | AWS PaaS (Serverless) |
| **Base de Datos** | PostgreSQL en contenedores | PostgreSQL en contenedores | Amazon RDS PostgreSQL | Amazon RDS PostgreSQL | Amazon RDS PostgreSQL |
| **Almacenamiento** | Volúmenes Docker locales | Volúmenes EBS | Amazon S3 | Amazon S3 | Amazon S3 |
| **Balanceador** | Nginx (contenedor) | Nginx (instancia EC2) | ALB | ALB Multi-AZ | ALB Multi-AZ |
| **Escalabilidad** | Manual | Manual | Automática (ASG Core) | Automática (ASG Core + Workers) | Automática (ECS Service Auto Scaling) |
| **Alta Disponibilidad** | No | No | Sí (ALB) | Sí (ALB + Multi-AZ) | Sí (Multi-AZ Gestionado) |
| **Message Broker** | RabbitMQ (contenedor) | RabbitMQ (instancia EC2) | RabbitMQ (instancia EC2) | Amazon SQS (gestionado) | Amazon SQS (gestionado) |
| **Workers** | Celery (contenedor) | Celery (instancia EC2) | Celery (instancia EC2) | Celery (ASG) | Celery (ECS Fargate) |
| **Infraestructura** | Docker Compose | Terraform + EC2 | Terraform + AWS | Terraform + AWS | Terraform + ECS Fargate |
| **Observabilidad** | Prometheus, Grafana, Loki | Prometheus, Grafana, Loki | CloudWatch | CloudWatch | CloudWatch + Container Insights |

---

## Entrega 1: API REST y Procesamiento Asíncrono

**Objetivo:** Implementación de una API REST escalable con orquestación de tareas asíncronas en ambiente local con Docker Compose.

### Características

- API RESTful con 9 endpoints
- Autenticación JWT con refresh tokens
- Procesamiento asíncrono con Celery y RabbitMQ
- PostgreSQL en contenedores Docker
- Almacenamiento local en volúmenes Docker
- Stack de observabilidad (Prometheus, Grafana, Loki)
- Nginx como reverse proxy

### Inicio Rápido

```bash
# Prerrequisitos
- Docker Desktop (o Docker Engine)
- Docker Compose

# Clonar el repositorio
git clone https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube.git
cd misw4204-2025-15-desarrollo-de-sw-en-la-nube

# Levantar todos los servicios
docker compose up -d

# Verificar estado
docker compose ps

# Cargar datos de prueba (opcional)
docker compose exec anb_api python seed_data.py
```

### Acceso a Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Swagger API Principal | http://localhost:8080/api/docs | - |
| Swagger Autenticación | http://localhost:8080/auth/docs | - |
| (Migrado) RabbitMQ Management | Reemplazado por AWS SQS | N/A |
| Grafana | http://localhost:8080/grafana/ | admin / admin |

### Documentación

- [Documentación Completa - Entrega 1](docs/Entrega_1/README.md)
- [Wiki del Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki)

---

## Entrega 2: Despliegue en AWS

**Objetivo:** Migración de la aplicación de Docker Compose local a AWS, desplegando en múltiples instancias EC2.

### Características

- 6 instancias EC2 independientes (t3.micro)
- PostgreSQL en contenedores distribuidos
- Nginx como reverse proxy en instancia dedicada
- Volúmenes EBS para almacenamiento
- Infraestructura como Código con Terraform
- Despliegue automatizado con user-data scripts
- Stack de observabilidad distribuido

### Componentes Desplegados

1. **Web Server**: Nginx + reverse proxy
2. **Core Services**: API Core + Auth Service
3. **Worker**: Celery + FFmpeg para procesamiento
4. **Database**: PostgreSQL (contenedores)
5. **Message Queue**: RabbitMQ
6. **Observability**: Prometheus + Grafana + Loki

### Inicio Rápido

```bash
# Prerrequisitos
- Terraform instalado
- AWS CLI configurado
- Credenciales de AWS Academy

# Configurar variables
cd infra
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus valores

# Desplegar infraestructura
terraform init
terraform plan
terraform apply

# Obtener IPs de las instancias
terraform output
```

### Documentación

- [Documentación Completa - Entrega 2](docs/Entrega_2/README.md)
- [Cambios vs Entrega 1](docs/Entrega_2/cambios.md)
- [Infraestructura Terraform](infra/README.md)

---

## Entrega 3: Escalabilidad en la Capa Web

**Objetivo:** Implementación de escalabilidad automática y servicios gestionados de AWS para alta disponibilidad y escalabilidad.

### Características

- **Application Load Balancer (ALB)**: Balanceador de carga público con health checks
- **Auto Scaling Group (ASG)**: Escalado automático del Core API (1-3 instancias)
- **Amazon RDS PostgreSQL**: 2 instancias gestionadas (core y auth)
- **Amazon S3**: Almacenamiento de objetos para videos
- **CloudWatch**: Monitoreo y métricas de AWS
- Alta disponibilidad multi-AZ
- Recuperación automática ante fallos

### Cambios Principales vs Entrega 2

- Eliminada instancia Web Nginx → Reemplazada por ALB
- Eliminada instancia DB EC2 → Reemplazada por RDS
- Almacenamiento EBS → Migrado a S3
- Instancias fijas Core API → Auto Scaling Group
- Observabilidad mejorada con CloudWatch

### Inicio Rápido

```bash
# Prerrequisitos
- Terraform instalado
- AWS CLI configurado
- Credenciales de AWS Academy con permisos para RDS, S3, ALB, ASG
- Assets del worker (watermark.png, inout.mp4) en worker/assets/

# Configurar variables
cd infra
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars:
# - rds_password: Contraseña para RDS
# - assets_inout_path: Ruta a worker/assets/inout.mp4
# - assets_wm_path: Ruta a worker/assets/watermark.png

# Desplegar infraestructura
terraform init
terraform plan
terraform apply

# Obtener DNS del ALB
terraform output alb_dns_name
```

### Acceso a Servicios

Una vez desplegado, accede a los servicios a través del DNS del ALB:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API Principal | http://`<alb-dns>`/api/docs | - |
| Auth Service | http://`<alb-dns>`/auth/docs | - |
| Grafana | http://`<alb-dns>`/grafana/ | admin / admin |
| Prometheus | http://`<alb-dns>`/prometheus/ | - |
| (Migrado) RabbitMQ | Reemplazado por AWS SQS | N/A |

### Documentación

- [Documentación Completa - Entrega 3](docs/entrega3/entrega_3.md)
- [Arquitectura Actual]([entrega3/ARQUITECTURA_ACTUAL.md](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-3#arquitectura-entrega-3))
- [Infraestructura Terraform](infra/README.md)

---

## Entrega 4: Escalabilidad en la Capa Batch/Worker

**Objetivo:** Implementación de escalabilidad automática en la capa de procesamiento batch (workers) utilizando servicios gestionados de AWS, completando la transformación del sistema hacia una arquitectura cloud-native totalmente escalable y de alta disponibilidad.

### Características

- **Auto Scaling Group - Workers**: Escalado automático del procesamiento batch (1-3 instancias t3.large)
- **Amazon SQS**: Sistema de mensajería gestionado que reemplaza RabbitMQ
- **Dead Letter Queue (DLQ)**: Manejo automático de mensajes fallidos
- **Multi-AZ Core API**: Despliegue en múltiples zonas de disponibilidad (us-east-1a y us-east-1b)
- **Alta Disponibilidad**: Sistema resiliente ante fallos de zona completa
- Escalabilidad automática tanto en capa web como en capa de procesamiento

### Cambios Principales vs Entrega 3

- Eliminada instancia Worker EC2 fija → Reemplazada por Auto Scaling Group
- Eliminado RabbitMQ EC2 → Reemplazado por Amazon SQS
- Core API desplegado en múltiples zonas de disponibilidad (us-east-1a y us-east-1b)
- ASG Core API expandido: 2-4 instancias (antes 1-3)
- Alta disponibilidad completa mediante despliegue multi-AZ

### Inicio Rápido

```bash
# Prerrequisitos
- Terraform instalado
- AWS CLI configurado
- Credenciales de AWS Academy con permisos para RDS, S3, ALB, ASG, SQS
- Assets del worker (watermark.png, inout.mp4) en worker/assets/

# Usar release v4.0.0 (desde main)
git checkout v4.0.0
# O usar main directamente
git checkout main

# Configurar variables
cd infra
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars:
# - rds_password: Contraseña para RDS
# - assets_inout_path: Ruta a worker/assets/inout.mp4
# - assets_wm_path: Ruta a worker/assets/watermark.png

# Desplegar infraestructura
terraform init
terraform plan
terraform apply

# Obtener DNS del ALB
terraform output alb_dns_name
```

### Acceso a Servicios

Una vez desplegado, accede a los servicios a través del DNS del ALB:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API Principal | http://`<alb-dns>`/api/docs | - |
| Auth Service | http://`<alb-dns>`/auth/docs | - |
| Grafana | http://`<alb-dns>`/grafana/ | admin / admin |
| Prometheus | http://`<alb-dns>`/prometheus/ | - |
| Amazon SQS | Console AWS / Terraform output | N/A |

### Componentes Principales

**Auto Scaling Group - Core API**
- Capacidad: 2-4 instancias t3.small
- Política de escalado: CPU promedio 50%
- Zonas: us-east-1a y us-east-1b (multi-AZ)
- Health check: ELB-based mediante `/api/health`

**Auto Scaling Group - Workers** (Nuevo)
- Capacidad: 1-3 instancias t3.large
- Política de escalado: CPU promedio 60%
- Optimizado para procesamiento intensivo de video con FFmpeg
- Health check: EC2-based

**Amazon SQS** (Nuevo)
- Cola principal: `video_tasks`
- Dead Letter Queue (DLQ): Manejo de mensajes fallidos
- Long polling: 20 segundos
- Visibilidad timeout: 60 segundos
- Retención: 14 días

### Rendimiento

**Core API** (basado en pruebas de carga):
- 4MB: 35 requests/segundo, p95 latencia de 305ms, 100% success rate
- 50MB: 2.7 requests/segundo, p95 latencia de 4.6s, 100% success rate
- 100MB: 1.46 requests/segundo, p95 latencia de 9s, 100% success rate

**Workers** (throughput normalizado):
- 4MB: 22 MB/minuto (5.5 videos/min, 1,320 MB/hora)
- 50MB: 142.5 MB/minuto (2.85 videos/min, 8,550 MB/hora)
- 100MB: ~140 MB/minuto estimado (~1.4 videos/min, ~8,400 MB/hora)

**Confiabilidad**: 99.90-100% success rate bajo carga sostenida

### Documentación

- [Documentación Completa - Entrega 4](docs/entrega4/entrega4.md)
- [Pruebas de Carga - Entrega 4](capacity-planning/pruebas_de_carga_entrega4.md)
- [Wiki del Proyecto - Entrega 4](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-4)
- [Infraestructura Terraform](infra/README.md)

---

## Entrega 5: Despliegue en PaaS (ECS)

**Objetivo:** Migración de la arquitectura IaaS (EC2) a una arquitectura PaaS utilizando **Amazon ECS con Fargate**, eliminando la gestión directa de servidores y mejorando la eficiencia operativa.

### Características

- **Amazon ECS (Fargate)**: Orquestación de contenedores sin servidor (Serverless Compute)
- **Servicios ECS**: Core API y Workers desplegados como servicios escalables
- **Tareas ECS**: Auth Service desplegado como tarea independiente
- **Application Load Balancer (ALB)**: Balanceo de carga para servicios ECS
- **Amazon SQS**: Integración nativa para comunicación asíncrona
- **Alta Disponibilidad**: Despliegue multi-AZ gestionado por AWS

### Cambios Principales vs Entrega 4

- **EC2 ASG → ECS Fargate**: Reemplazo de instancias EC2 por tareas Fargate gestionadas
- **Gestión de Infraestructura**: Eliminación de scripts `user-data` complejos en favor de definiciones de tareas (Task Definitions)
- **Escalado**: Auto-scaling basado en métricas de servicio ECS (CPU/Memoria)
- **Eficiencia**: Mayor throughput en procesamiento de video (Workers) gracias a menor overhead de SO

### Inicio Rápido

La infraestructura de esta entrega se encuentra en el directorio `infra-ecs`.

```bash
# Prerrequisitos
- Terraform instalado
- AWS CLI configurado

# Desplegar infraestructura ECS
cd infra-ecs
terraform init
terraform apply

# Ver outputs (ALB DNS)
terraform output
```

### Documentación

- [Guía de Infraestructura ECS](infra-ecs/README.md)
- [Análisis de Pruebas de Carga - Entrega 5](capacity-planning/pruebas_de_carga_entrega5.md)
- [Wiki del Proyecto - Entrega 5](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-5)
- [Análisis de Calidad de Código (SonarQube)](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/sonar-entrega-5)

---

## Estructura del Proyecto

```
.
├── core/                  # API principal (FastAPI)
│   ├── app/               # Código de la aplicación
│   ├── storage/           # Almacenamiento de videos (local o S3)
│   ├── tests/             # Tests unitarios
│   └── README.md          # Documentación de desarrollo local
├── auth_service/          # Servicio de autenticación
│   ├── app/               # Código de autenticación
│   ├── tests/             # Tests unitarios
│   └── README.md          # Documentación de desarrollo local
├── worker/                # Worker de procesamiento (Celery)
│   ├── tasks/             # Tareas de Celery
│   ├── assets/            # Assets (watermark, intro/outro)
│   └── README.md          # Documentación de desarrollo local
├── infra/                 # Infraestructura como Código (Terraform)
│   ├── main.tf            # Definición de recursos AWS
│   ├── userdata.sh.tftpl  # Scripts de configuración
│   └── README.md          # Guía de despliegue
├── nginx/                 # Configuración de Nginx (Entrega 1)
├── rabbitmq/              # (Deprecado) Configuración legacy de RabbitMQ
├── observability/         # Stack de observabilidad
│   ├── grafana/           # Configuración de Grafana
│   ├── prometheus/        # Configuración de Prometheus
│   └── loki/              # Configuración de Loki
├── collections/           # Colección de Postman
│   └── ANB_Basketball_API.postman_collection.json
├── docs/                  # Documentación del proyecto
│   ├── Entrega_1/         # Documentación Entrega 1
│   ├── Entrega_2/         # Documentación Entrega 2
│   ├── entrega3/          # Documentación Entrega 3
│   └── entrega4/          # Documentación Entrega 4
├── capacity-planning/     # Plan y análisis de pruebas de carga
│   ├── plan_de_pruebas.md
│   ├── pruebas_de_carga_entrega3.md
│   └── pruebas_de_carga_entrega4.md
├── compose.yaml           # Docker Compose (Entrega 1)
├── docker-compose.multihost.yml  # Docker Compose multihost (Entrega 2-3)
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
- PostgreSQL 15 (contenedores o RDS)

### Procesamiento Asíncrono
- Celery (task queue)
- Amazon SQS (message broker gestionado - Entrega 4)
- RabbitMQ (deprecado en Entrega 4, reemplazado por SQS)
- FFmpeg (procesamiento de video)

### Infraestructura
- Docker y Docker Compose (Entrega 1)
- Terraform (Entrega 2-4)
- AWS EC2, RDS, S3, ALB, ASG, SQS (Entrega 2-4)
- Nginx 1.25 (reverse proxy - Entrega 1-2, deprecado en Entrega 3)

### Observabilidad
- Grafana (visualización)
- Prometheus (métricas)
- Loki (logs)
- CloudWatch (métricas AWS - Entrega 3-4)


---

## Comandos Útiles
## Variables de Entorno Clave (SQS)

Para la nueva integración con AWS SQS se requieren las siguientes variables de entorno en `.env`:

```
SQS_BROKER_URL=<URL o ARN de la cola principal>
SQS_QUEUE_NAME=<Nombre de la cola>
AWS_REGION=<Región AWS, ej. us-east-1>
AWS_ACCESS_KEY_ID=<Clave de acceso>
AWS_SECRET_ACCESS_KEY=<Secreto>
```

En la configuración de Celery se usa `CELERY_BROKER_URL=${SQS_BROKER_URL}`. RabbitMQ ya no es necesario.

### Entrega 1 (Docker Compose)

```bash
# Levantar servicios
docker compose up -d

# Ver logs
docker compose logs -f anb_api
docker compose logs -f worker

# Detener servicios
docker compose down

# Reconstruir servicios
docker compose up -d --build --force-recreate
```

### Entrega 2-4 (Terraform)

```bash
# Inicializar Terraform
cd infra
terraform init

# Planificar cambios
terraform plan

# Aplicar cambios
terraform apply

# Ver outputs (incluye ALB DNS, SQS queue URLs)
terraform output

# Verificar estado de recursos
terraform show

# Destruir infraestructura
terraform destroy
```

**Nota**: Para la Entrega 4, asegúrate de tener permisos para SQS y que los assets del worker estén disponibles en `worker/assets/`.


---

## Notas Importantes

### AWS Academy

Este proyecto utiliza **AWS Academy** para el despliegue en la nube. Las limitaciones incluyen:

- Máximo 9 instancias EC2 simultáneas
- Máximo 32 vCPUs
- Credenciales temporales (requieren renovación)
- Sin acceso completo a IAM

### Versiones y Tags

- **v1.0.0**: Entrega 1 - API REST y Procesamiento Asíncrono
- **v2.0.0**: Entrega 2 - Despliegue en AWS
- **v3.0.0**: Entrega 3 - Escalabilidad en la Capa Web
- **v4.0.0**: Entrega 4 - Escalabilidad en la Capa Batch/Worker




