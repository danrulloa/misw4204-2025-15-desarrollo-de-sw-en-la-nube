# ANB Rising Stars Showcase

**Proyecto Académico** - Sistema de Procesamiento de Videos y Votaciones

**Curso:** MISW4204 - Desarrollo de Software en la Nube  
**Universidad:** Universidad de los Andes  
**Año:** 2025  
**Equipo:** Daniel Ulloa, David Cruz, Frans Taboada, Nicolás Infante

---

## 📋 Descripción del Proyecto

ANB Rising Stars Showcase es un sistema completo para la gestión de videos y votaciones de jugadores de baloncesto de la Asociación Nacional de Baloncesto (ANB). El sistema permite a jugadores aficionados subir videos de sus habilidades, procesarlos automáticamente y permitir que el público vote por sus favoritos.

### Características Principales

- ✅ API RESTful con 9 endpoints documentados en OpenAPI/Swagger
- ✅ Autenticación y autorización con JWT y refresh tokens
- ✅ Procesamiento asíncrono de videos (redimensionamiento, conversión, marca de agua)
- ✅ Sistema de votación pública con rankings dinámicos
- ✅ Observabilidad completa con métricas, logs y traces distribuidos
- ✅ Pruebas unitarias con cobertura superior al 80%
- ✅ Colección Postman con tests automatizados

---

## 🎯 Versiones del Proyecto

Este proyecto ha evolucionado a lo largo de **3 entregas académicas**, cada una representando una versión diferente del sistema con mejoras en escalabilidad, infraestructura y servicios gestionados.

### Resumen Comparativo

| Aspecto | **Entrega 1** | **Entrega 2** | **Entrega 3** |
|---------|---------------|---------------|---------------|
| **Ambiente** | Docker Compose Local | AWS EC2 (6 instancias) | AWS con servicios gestionados |
| **Base de Datos** | PostgreSQL en contenedores | PostgreSQL en contenedores | Amazon RDS PostgreSQL |
| **Almacenamiento** | Volúmenes Docker locales | Volúmenes EBS | Amazon S3 |
| **Balanceador** | Nginx (contenedor) | Nginx (instancia EC2) | Application Load Balancer (ALB) |
| **Escalabilidad** | Manual (recrear contenedores) | Manual (recrear instancias) | Automática (Auto Scaling Group) |
| **Alta Disponibilidad** | No | No | Sí (ALB + Multi-AZ) |
| **Infraestructura** | Docker Compose | Terraform + EC2 | Terraform + AWS (RDS, S3, ALB, ASG) |
| **Observabilidad** | Prometheus, Grafana, Loki | Prometheus, Grafana, Loki | Prometheus, Grafana, Loki + CloudWatch |

---

## 📦 Entrega 1: API REST y Procesamiento Asíncrono

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
| RabbitMQ Management | http://localhost:15672 | rabbit / rabbitpass |
| Grafana | http://localhost:8080/grafana/ | admin / admin |

### Documentación

- [Documentación Completa - Entrega 1](docs/Entrega_1/README.md)
- [Wiki del Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki)

---

## ☁️ Entrega 2: Despliegue en AWS

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

## 🚀 Entrega 3: Escalabilidad en la Capa Web

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

- ✅ Eliminada instancia Web Nginx → Reemplazada por ALB
- ✅ Eliminada instancia DB EC2 → Reemplazada por RDS
- ✅ Almacenamiento EBS → Migrado a S3
- ✅ Instancias fijas Core API → Auto Scaling Group
- ✅ Observabilidad mejorada con CloudWatch

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
| RabbitMQ | http://`<alb-dns>`/rabbitmq/ | rabbit / rabbitpass |

### Documentación

- [Documentación Completa - Entrega 3](docs/entrega3/entrega_3.md)
- [Arquitectura Actual]([entrega3/ARQUITECTURA_ACTUAL.md](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-3#arquitectura-entrega-3))
- [Infraestructura Terraform](infra/README.md)

---

## 📚 Estructura del Proyecto

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
├── rabbitmq/              # Configuración de RabbitMQ
├── observability/         # Stack de observabilidad
│   ├── grafana/           # Configuración de Grafana
│   ├── prometheus/        # Configuración de Prometheus
│   └── loki/              # Configuración de Loki
├── collections/           # Colección de Postman
│   └── ANB_Basketball_API.postman_collection.json
├── docs/                  # Documentación del proyecto
│   ├── Entrega_1/         # Documentación Entrega 1
│   ├── Entrega_2/         # Documentación Entrega 2
│   └── entrega3/          # Documentación Entrega 3
├── capacity-planning/     # Plan y análisis de pruebas de carga
│   ├── plan_de_pruebas.md
│   └── pruebas_de_carga_entrega3.md
├── compose.yaml           # Docker Compose (Entrega 1)
├── docker-compose.multihost.yml  # Docker Compose multihost (Entrega 2-3)
└── README.md              # Este archivo
```

---

## 🛠️ Stack Tecnológico

### Backend y APIs
- Python 3.12
- FastAPI
- Pydantic (validación)
- JWT (autenticación)

### Bases de Datos
- PostgreSQL 15 (contenedores o RDS)

### Procesamiento Asíncrono
- Celery (task queue)
- RabbitMQ 3.10 (message broker)
- FFmpeg (procesamiento de video)

### Infraestructura
- Docker y Docker Compose (Entrega 1)
- Terraform (Entrega 2-3)
- AWS EC2, RDS, S3, ALB, ASG (Entrega 2-3)
- Nginx 1.25 (reverse proxy - Entrega 1-2)

### Observabilidad
- Grafana (visualización)
- Prometheus (métricas)
- Loki (logs)
- CloudWatch (métricas AWS - Entrega 3)


---

## 🔧 Comandos Útiles

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

### Entrega 2-3 (Terraform)

```bash
# Inicializar Terraform
cd infra
terraform init

# Planificar cambios
terraform plan

# Aplicar cambios
terraform apply

# Ver outputs
terraform output

# Destruir infraestructura
terraform destroy
```


---

## 📝 Notas Importantes

### AWS Academy

Este proyecto utiliza **AWS Academy** para el despliegue en la nube. Las limitaciones incluyen:

- Máximo 9 instancias EC2 simultáneas
- Máximo 32 vCPUs
- Credenciales temporales (requieren renovación)
- Sin acceso completo a IAM

### Versiones y Tags

- **v1.0.0**: Entrega 1 - API REST y Procesamiento Asíncrono
- **v2.0.0**: Entrega 2 - Despliegue en AWS
- **v3.0.0**: Entrega 3 - Escalabilidad en la Capa Web (rama `develop`)

---

## 👥 Equipo

| Nombre | Correo Institucional |
|--------|---------------------|
| Daniel Ricardo Ulloa Ospina | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |



## 
Este es un proyecto académico desarrollado para el curso MISW4204 - Desarrollo de Software en la Nube de la Universidad de los Andes.

---

**Última actualización:** Noviembre 2025
