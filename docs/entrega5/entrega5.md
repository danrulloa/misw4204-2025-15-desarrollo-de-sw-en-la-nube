## [--> LINK AL VIDEO DE PRESENTACIÓN DE ENTREGA 5 FINAL<--](https://uniandes-my.sharepoint.com/:v:/g/personal/d_ulloa_uniandes_edu_co/IQAQaigUjv2OTaR3vP-0RDT1AZ33luREbvHv9Ryg_KZoQkQ?e=1INiym)


https://github.com/user-attachments/assets/42f604bb-f2f1-4b2b-9546-ea218e30177a

# Cambios Arquitectónicos: Semana 6 → Semana 8 

Este documento resume los cambios y mejoras de arquitectura entre las versiones **semana 6** y **semana 8** de la infraestructura ANB, con énfasis en la migración desde un despliegue basado en **EC2** a uno gestionado por **Amazon ECS sobre Fargate**.

---

## 1. Resumen del cambio clave

- **Semana 6**  
  - Servicios desplegados sobre **EC2** (con Docker / docker-compose y/o ASG).
  - Escalamiento a nivel de instancia EC2.
  - Mayor acoplamiento entre infraestructura y configuración de los contenedores.

- **Semana 8**  
  - Migración del plano de cómputo a **Amazon ECS (Fargate)**:
    - **Cluster ECS:** `anb-cluster`.
    - **Servicios ECS Fargate:** `core`, `auth`, `worker`.
    - **Task Definitions** para cada servicio con CPU/Memoria declaradas.
  - El ALB ahora enruta tráfico directamente a **tasks Fargate** mediante target groups tipo `ip`.
  - Escalamiento automático a nivel de **ECS Service DesiredCount** usando **Application Auto Scaling**.

---

## 2. Estado anterior (Semana 6) – visión general

En la versión de semana 6, el despliegue seguía este enfoque (alto nivel):

- **Capa de cómputo:**
  - Core/API y Auth desplegados en **EC2**.
  - Worker ejecutándose en EC2 consumiendo SQS/Celery.

- **Capa de datos y mensajería:**
  - Base de datos **RDS PostgreSQL**.
  - Mensajería mediante **SQS**.
  - Almacenamiento de videos en **S3**.

- **Balanceo de carga:**
  - Un **Application Load Balancer (ALB)** enruta tráfico a las instancias EC2.

Limitaciones:
- Escalado atado a EC2.
- Mayor manutención (Docker/compose en las instancias).
- Menor aislamiento entre servicios y la infraestructura subyacente.

---

## 3. Estado actual (Semana 8): Arquitectura ECS/Fargate

### 3.1 Roles e IAM (LabRole)

Se utiliza el rol predefinido **LabRole** de AWS Academy, evitando la necesidad de crear roles IAM.

Este rol es usado como:
- **task_role_arn**
- **execution_role_arn**

Dentro de todas las task definitions.

### 3.2 Red (VPC, Subnets, Routing)

- Se creó una **VPC dedicada** `10.0.0.0/16`.
- Dos **subredes públicas** (una por AZ).
- **Internet Gateway** y route table público.
- ECS/Fargate corre dentro de estas subnets con `assign_public_ip = true`.

### 3.3 Seguridad (Security Groups)

- **alb_sg**  
  - Permite tráfico HTTP 80 desde cualquier origen.
- **ecs_tasks_sg**  
  - Permite únicamente tráfico proveniente del ALB.
- **rds_sg**  
  - Permite PostgreSQL (5432) desde ECS tasks.
  - (Modo laboratorio) acceso abierto a DB desde internet.

### 3.4 Servicios compartidos: S3, SQS y RDS

- **S3**  
  Bucket `anb-videos-*` con assets del worker cargados automáticamente:
  - `assets/inout.mp4`
  - `assets/watermark.png`

- **SQS**  
  Cola Celery: `anb-celery-queue`.

- **RDS PostgreSQL**  
  - Instancia `db.t3.micro` accesible desde ECS.
  - Base de datos única para Core/Auth/Worker.

---

## 4. Cluster ECS y Logging

### ECS Cluster
- `anb-cluster` creado para ejecutar tasks Fargate.

### CloudWatch Logs
- Grupo `/ecs/anb-apps`.
- Logs por servicio con stream prefix: `core/`, `auth/`, `worker/`.

---

## 5. Application Load Balancer (ALB)

### Configuración del ALB
- Listener HTTP 80 → default 404.
- Target groups **tipo IP** para tareas Fargate.

### Ruteo
- `/api/*` → Core TG (`anb-core-tg`)
- `/auth/*` → Auth TG (`anb-auth-tg`)

---

## 6. Task Definitions

### Core API
- Task: `anb-core`
- CPU: `2048`, Memoria: `4096`
- Imagen: `ftaboadar/anb-core:latest`
- Variables:
  - `DATABASE_URL` → RDS
  - `CELERY_BROKER_URL = sqs://`
  - `SQS_QUEUE_NAME = video_tasks`
  - `JWT_SECRET`, `ALGORITHM`
  - `S3_BUCKET`

### Auth
- Task: `anb-auth`
- CPU: `512`, Memoria: `1024`
- Imagen: `ftaboadar/anb-auth:latest`
- Variables:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `TOKEN_EXPIRE`
  - `REFRESH_TOKEN_EXPIRE`

### Worker
- Task: `anb-worker`
- CPU: `2048`, Memoria: `4096`
- Imagen: `ftaboadar/anb-worker:latest`
- Variables:
  - `DB_URL_CORE`
  - `CELERY_BROKER_URL = sqs://`
  - `SQS_QUEUE_NAME = video_tasks`
  - `S3_BUCKET`, `S3_REGION`
  - `ANB_INOUT_PATH`, `ANB_WATERMARK_PATH`

---

## 7. ECS Services y Auto Scaling

### Servicios
- `anb-core-service`: integra con ALB (Puerto 8000).
- `anb-auth-service`: también con ALB.
- `anb-worker-service`: sin load balancer.

### Auto Scaling por CPU

- **Core**  
  - Min: 1  
  - Max: 3  
  - Target: 60% CPU

- **Worker**  
  - Min: 1  
  - Max: 3  
  - Target: 60% CPU

---

## 8. Impacto Global

- **Completa migración de EC2 a ECS/Fargate.**
- Reducción total de la manutención de servidores EC2.
- Mejor aislamiento y separación entre infraestructura y contenedores.
- Escalado más granular basado en tareas.
- Logs centralizados en CloudWatch.
- Seguridad reforzada mediante SG separados.
- Infraestructura declarativa y reproducible 100% en Terraform.

---

## 9. Diagramas de Arquitectura

### 9.1 Diagrama de Componentes

<img width="1626" height="1020" alt="bLDRRkis4FtNAWR-QN81rO-a5wc15jUFFWeuXHF5zO-1O4HD5JKIgPAK4xV8RnVGVNG3_SrEkfAEACfNCO8y4i2WPiuvSp0y_6GiQbiLUM0pcnDCVfv22FCCKuq5Ga8m9rFc6QKLmL541Kg4CuPyDulwtwDEqT9n4A2mIaDlPIhKcO8rnJr00oj3EWX4hge4UfDrr8C_Wm10AjRj_RASmN3mfVll3pzk9Ceu9672RIaScm4D" src="https://github.com/user-attachments/assets/b77da422-aec0-40cd-be24-7d8037d6ff37" />

### 9.2 Diagrama de Despliege

<img width="1804" height="869" alt="fLHjRjj64FslKmnKe9NIAYhW0ZM4n0WbCwrH-SEINQC00M6udD2ioLrwTsd5AGBqLm_GdYEdo4roaivolR9aomsAo8PDpSnxyuRxPbyPYzesLTcnXIq9egCnVFhp7zWlCDTO8MG44rNLIfAqPA0tfmebmYuC89xCXwzHvsYft-cOgqBMo1WGeNvkRvbIax0eyvBMIbOn-AC3C4PnbMlLo6oYIgLVlC2bsTk3hrx_w7vSWT8P" src="https://github.com/user-attachments/assets/68862573-6af4-4ec5-8087-b65a4de9775b" />


La documentación detallada de esta entrega se encuentra disponible en la Wiki del proyecto:

- **[Wiki: Entrega 5 - Despliegue en PaaS](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-5)**

Esta página en la Wiki contiene:
- Descripción de la arquitectura ECS Fargate.
- Diagramas de despliegue.
- Detalles de configuración de servicios y tareas.
- Estrategia de auto-escalado.

Para ver el análisis de pruebas de carga, consulta:
- [Análisis de Pruebas de Carga - Entrega 5](../../capacity-planning/pruebas_de_carga_entrega5.md)
