# Infraestructura ECS para ANB

Este directorio contiene el código Terraform para desplegar la aplicación ANB utilizando contenedores en AWS ECS (Fargate), con una arquitectura de alta disponibilidad y auto-escalado.

## Prerrequisitos

1.  Tener [Terraform](https://developer.hashicorp.com/terraform/install) instalado en tu máquina.
2.  Tener credenciales activas de AWS (AWS Academy o cuenta propia).

## Configuración de Credenciales

El archivo `terraform.tfvars` es donde se definen los secretos y configuraciones específicas. Asegúrate de que tenga este formato:

```hcl
aws_region        = "us-east-1"
aws_access_key    = "TU_ACCESS_KEY"
aws_secret_key    = "TU_SECRET_KEY"
aws_session_token = "TU_SESSION_TOKEN"
db_username       = "postgres"
db_password       = "un_password_seguro"
jwt_secret        = "un_secreto_para_tokens"
```

> **Nota:** Nunca subas el archivo `terraform.tfvars` con credenciales reales a un repositorio público.

## Cómo Aprovisionar (Desplegar)

Sigue estos pasos en tu terminal dentro de la carpeta `infra-ecs`:

1.  **Inicializar:** Descarga los proveedores necesarios (AWS).
    ```bash
    terraform init
    ```

2.  **Planificar:** Verifica qué recursos se van a crear. Si hay errores de sintaxis o credenciales, aparecerán aquí.
    ```bash
    terraform plan
    ```

3.  **Aplicar:** Crea la infraestructura en AWS.
    ```bash
    terraform apply -auto-approve
    ```
    *   Escribe `yes` cuando te pregunte `Do you want to perform these actions?`.
    *   ⏳ **Tiempo estimado:** 5 a 10 minutos (la base de datos RDS es lo que más tarda).

### Resultado
Al finalizar, Terraform te mostrará los `Outputs` importantes:
*   `alb_dns_name`: La URL pública de tu API (ej. `http://anb-alb-xxxx.us-east-1.elb.amazonaws.com`).
*   `rds_endpoint`: La dirección de la base de datos.
*   `s3_bucket_name`: El nombre del bucket creado.

## Cómo Destruir (Limpiar)

Para borrar **todos** los recursos creados y evitar costos adicionales:

```bash
terraform destroy -auto-approve
```
*   Escribe `yes` para confirmar.
*   Esto eliminará el Cluster, Servicios, Base de Datos, Load Balancer, etc.

## Arquitectura Desplegada

*   **ECS Cluster:** `anb-cluster`
*   **Servicios Fargate:**
    *   `core`: API principal (Auto-scaling 1-3 tareas).
    *   `auth`: Servicio de autenticación (1 tarea).
    *   `worker`: Procesamiento de video (Auto-scaling 1-3 tareas).
*   **Networking:** VPC propia, Subnets públicas en Multi-AZ, Application Load Balancer (ALB).
*   **Datos:** RDS PostgreSQL (db.t3.micro), S3 Bucket, SQS Queue.
*   **Observabilidad:** CloudWatch Logs (`/ecs/anb-apps`).
