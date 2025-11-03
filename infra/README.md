# README — Despliegue ANB en AWS Academy (Lab)

## 0) Contexto y arquitectura

Este lab levanta **5 instancias EC2** (o 6 si se incluye la instancia DB legacy) con Ubuntu, más **2 instancias RDS** para bases de datos PostgreSQL y un **bucket S3** para almacenamiento de videos. La instalación puede ser:

- **Automática** (recomendada): vía `user-data` (cloud-init) se instala Docker/Compose, se clona el repo y se levanta el stack multihost.
- **Manual**: copias el paquete y ejecutas `docker compose` por perfiles.

El despliegue multihost usa `docker-compose.multihost.yml` con **profiles** por rol.

**Topología actualizada:**

### Instancias EC2 (5-6 VMs)
- **CORE**: anb_api + anb-auth-service + cAdvisor + promtail  
- **DB** (legacy, opcional): PostgreSQL local - **Ya no se usa si RDS está configurado**
- **MQ**: RabbitMQ (broker/UI) + cAdvisor + promtail  
- **WORKER**: Celery worker + cAdvisor + promtail  
- **OBS**: Prometheus + Grafana + Loki

### Servicios AWS gestionados
- **RDS PostgreSQL**: 2 instancias gestionadas (`anb-core-rds` y `anb-auth-rds`)
  - Reemplazan las bases de datos locales de la instancia DB
  - Configuradas con security group dedicado
  - Storage encriptado, backups automáticos (7 días)
- **S3 Bucket**: Almacenamiento de videos (`anb-basketball-bucket-*`)
  - Carpeta `uploads/` para videos originales
  - Carpeta `processed/` para videos procesados
   - Destrucción: configurado con `force_destroy = true` para eliminar el bucket aunque tenga objetos y versiones
- **Application Load Balancer (ALB)**: Balanceador de carga público
  - Recibe tráfico HTTP en puerto 80
  - Distribuye carga a instancias Core
  - Routing a servicios de observabilidad (Grafana, Prometheus, Loki, RabbitMQ UI)

**Security Groups (7):**
- `alb` - Application Load Balancer (HTTP 80 público)
- `core` - Instancia Core (API + Auth)
- `db` - Instancia DB legacy (solo si se mantiene)
- `worker` - Instancia Worker
- `mq` - Instancia RabbitMQ
- `obs` - Instancia Observabilidad
- `rds` - RDS PostgreSQL (Core y Auth comparten este SG)

---

## Cambios principales en `main.tf`

### Recursos agregados

1. **RDS PostgreSQL** (2 instancias):
   - `aws_db_instance.core` - Base de datos para el API Core
   - `aws_db_instance.auth` - Base de datos para el servicio de autenticación
   - `aws_db_subnet_group.anb_rds` - Subnet group para RDS (requiere al menos 2 AZs)
   - `aws_security_group.rds` - Security group que permite tráfico desde instancias Core y Worker en puerto 5432

2. **S3 Bucket**:
   - `aws_s3_bucket.anb_videos` - Bucket con nombre único (`anb-basketball-bucket-*`)
   - Configurado con versioning, encriptación (AES256) y bloqueo de acceso público

3. **Application Load Balancer (ALB)**:
   - `aws_lb.public` - Load balancer público HTTP (puerto 80)
   - `aws_lb_target_group.core_api` - Target group para instancias Core (API en puerto 8000)
   - `aws_lb_target_group.core_auth` - Target group para instancias Core (Auth en puerto 8001)
   - `aws_lb_target_group.obs_*` - Target groups para servicios de observabilidad (Grafana, Prometheus, Loki)
   - `aws_lb_target_group.mq_ui` - Target group para RabbitMQ UI
   - Listeners y reglas de routing para distribuir tráfico según paths (`/api/*`, `/auth/*`, `/grafana/*`, etc.)

### Variables agregadas

- `rds_password` (sensitive) - Contraseña para las bases de datos RDS
- `rds_instance_class` - Tipo de instancia RDS (default: `db.t3.micro`)
- `repo_branch` - Rama del repositorio a clonar (default: `develop`)

#### Variables para assets del Worker (obligatorias con default)
- `assets_inout_path` (string) Ruta local del archivo de intro/outro para subir a S3 durante `terraform apply`. Por defecto apunta a `../worker/assets/inout.mp4`.
- `assets_wm_path` (string) Ruta local del archivo de watermark para subir a S3 durante `terraform apply`. Por defecto apunta a `../worker/assets/watermark.png`.
- `assets_inout_key` (string, default: `assets/inout.mp4`) Clave destino en S3 para el asset de intro/outro.
- `assets_wm_key` (string, default: `assets/watermark.png`) Clave destino en S3 para el asset de watermark.

### Cambios en `userdata.sh.tftpl`

El script de user-data ahora:
- Detecta si hay endpoints RDS configurados y los usa en lugar de la instancia DB local
- Configura `STORAGE_BACKEND=s3` si se proporciona `s3_bucket`
- Incluye configuración de S3 (bucket, region, prefixes)
- Pasa el DNS del ALB para configuración de Loki
- Hace checkout de la rama especificada en `repo_branch`

### Outputs agregados

- `alb_dns_name` - DNS del Application Load Balancer
- `rds_endpoints` - Endpoints de RDS (Core y Auth)
- `rds_addresses` - Direcciones IP/hostnames de RDS
- `s3_bucket_name` - Nombre del bucket S3 creado

---

## 1) Prerrequisitos

- **AWS CLI** instalado. Guía oficial: <https://docs.aws.amazon.com/es_es/cli/latest/userguide/getting-started-install.html>
- **Terraform** instalado. Guía: <https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli>
- **Tu PC local** (en AWS Academy, CloudShell suele estar restringido).
- Región recomendada: **us-east-1** (AZ: `us-east-1a`).
- Tipos sugeridos: `t3.micro` (o `t2.micro` si aplica en el lab).

---

## 2) Preparación local (variables de entorno y credenciales)

### 2.1 Obtener credenciales de AWS Academy

1. Ve a AWS Academy Lab
2. Abre la pestaña **"AWS Details"** o **"Credentials"**
3. Copia las credenciales temporales:
   - `aws_access_key_id`
   - `aws_secret_access_key`
   - `aws_session_token`

### 2.2 Configurar credenciales

**Opción A: Script PowerShell (Windows - Recomendado)**

Usa el script helper `setup-aws-env.ps1`:

```powershell
cd infra
.\setup-aws-env.ps1
```

**Opción B: Manual (bash/PowerShell)**

En **bash** (Linux/macOS):

```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_REGION="us-east-1"
```

En **PowerShell** (Windows):

```powershell
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
$env:AWS_REGION="us-east-1"
```

#### 2.2.1 Cómo usa Terraform estas variables ahora
No necesitas definir variables TF_VAR_*. Terraform leerá directamente estas variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN y AWS_REGION) y las inyectará a las instancias vía user-data.

### 2.3 Verificar credenciales

```bash
aws sts get-caller-identity
```

Debe mostrar tu Account ID (ej: `"Account": "758955011573"`).

> **Nota**: Las credenciales de sesión temporal expiran. Si fallan, obtén nuevas desde AWS Academy Lab.

---

## 3) Llave SSH

**Opción A (Recomendada - AWS Academy Lab):** Obtener llave desde AWS Academy

1. Ve a **AWS Academy Lab**
2. Abre la pestaña **AWS Details**
3. Busca la sección **"SSH Key"** o **"Download PEM"**
4. Copia todo el contenido de la llave privada (desde `-----BEGIN RSA PRIVATE KEY-----` hasta `-----END RSA PRIVATE KEY-----`)

**Guardar la llave en Windows:**
```powershell
# Crear carpeta .ssh si no existe
if (-not (Test-Path "$env:USERPROFILE\.ssh")) {
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh"
}

# Guardar la llave
# Pega el contenido completo de la llave en un editor de texto
# Guarda el archivo como: C:\Users\<tu-usuario>\.ssh\vockey.pem
# Asegúrate de que el archivo termine en .pem
```

**Guardar la llave en Linux/macOS:**
```bash
# Crear carpeta .ssh si no existe
mkdir -p ~/.ssh

# Guardar la llave
nano ~/.ssh/vockey.pem
# Pega el contenido completo y guarda (Ctrl+X, Y, Enter)

# Ajustar permisos (importante)
chmod 600 ~/.ssh/vockey.pem
```

**Verificar que la llave funciona:**
```bash
# Después de que las instancias EC2 estén creadas
ssh -i ~/.ssh/vockey.pem ubuntu@<IP_PUBLICA_EC2>
# O en Windows PowerShell:
ssh -i $env:USERPROFILE\.ssh\vockey.pem ubuntu@<IP_PUBLICA_EC2>
```

**Opción B:** Crear una nueva llave (solo si la de AWS Academy no funciona):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/anb_lab -N ""
```

Luego necesitarías importarla a AWS:
```bash
aws ec2 import-key-pair --key-name "anb-lab-key" --public-key-material fileb://~/.ssh/anb_lab.pub
```

### (Opcional) Importar Security Groups existentes

Si el instructor ya creó SGs y quieres **importarlos** al estado de Terraform:

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

aws ec2 describe-security-groups   --filters Name=vpc-id,Values=$VPC_ID Name=group-name,Values='anb-*-sg'   --query 'SecurityGroups[].{ID:GroupId,Name:GroupName}' --output table

# Limpia del estado los SG gestionados previamente (si aplica)
terraform state rm aws_security_group.web    2>/dev/null || true
terraform state rm aws_security_group.core   2>/dev/null || true
terraform state rm aws_security_group.db     2>/dev/null || true
terraform state rm aws_security_group.worker 2>/dev/null || true
terraform state rm aws_security_group.mq     2>/dev/null || true
terraform state rm aws_security_group.obs    2>/dev/null || true

# Importa tus SG (IDs de ejemplo; reemplaza por los tuyos)
terraform import aws_security_group.web    sg-01cb0a8bdb9b6ef2b
terraform import aws_security_group.core   sg-02514540403ee6516
terraform import aws_security_group.db     sg-01af27cfa756c56af
terraform import aws_security_group.worker sg-05621f0b6ce6c29d8
terraform import aws_security_group.mq     sg-05ca1bcc54417ef1d
terraform import aws_security_group.obs    sg-02ed299e0f587147e
```

> **Si no necesitas SGs preexistentes**, deja que Terraform los cree y **omite** esta sección.

---

## 4) Configurar variables de Terraform

### 4.1 Obtener tu IP pública

**Windows (PowerShell):**
```powershell
curl -s https://checkip.amazonaws.com
# Ejemplo: 186.81.58.137
```

**Linux/macOS (bash):**
```bash
curl -s https://checkip.amazonaws.com
```

### 4.2 Crear archivo `terraform.tfvars`

Crea el archivo `infra/terraform.tfvars` con el siguiente contenido completo:

```hcl
# ========================================
# Archivo: infra/terraform.tfvars
# ========================================
# ⚠️ ESTE ARCHIVO NO SE SUBE AL REPOSITORIO
# ⚠️ Contiene contraseñas sensibles

# Región de AWS
region = "us-east-1"

# Nombre de la llave SSH (obtenida desde AWS Academy Lab)
key_name = "vockey"

# IP pública del administrador (obtener con: curl -s https://checkip.amazonaws.com)
# Formato: IP/32 (ej: 186.81.58.137/32)
admin_cidr = "TU_IP_PUBLICA/32"  # ⚠️ ACTUALIZAR con tu IP pública

# ========================================
# Configuración RDS
# ========================================
# OBLIGATORIO: Contraseña segura para bases de datos PostgreSQL
# Requisitos: Mínimo 8 caracteres, incluir mayúsculas, minúsculas, números y símbolos
rds_password = "TuPasswordSeguro123!"  # ⚠️ CAMBIAR por una contraseña segura

# Tipo de instancia RDS (opcional, default: db.t3.micro)
rds_instance_class = "db.t3.micro"

# ========================================
# Configuración del repositorio (opcional)
# ========================================
# Rama del repositorio a clonar en las instancias EC2
# Por defecto usa "develop"
# repo_branch = "develop"

# URL del repositorio (si es diferente al default en main.tf)
# repo_url = "https://gitlab.com/tu-usuario/tu-repo.git"

# Archivo compose a usar (default: docker-compose.multihost.yml)
# compose_file = "docker-compose.multihost.yml"

# ========================================
# Subir assets del Worker a S3 (obligatorio)
# ========================================
# Rutas locales a los archivos (normalmente no necesitas cambiarlas)
# Por defecto: infra usa ../worker/assets/inout.mp4 y ../worker/assets/watermark.png
# assets_inout_path = "C:/ruta/custom/inout.mp4"
# assets_wm_path    = "C:/ruta/custom/watermark.png"
# Claves destino en el bucket S3 (puedes dejarlas por defecto)
# assets_inout_key = "assets/inout.mp4"
# assets_wm_key    = "assets/watermark.png"
```

**Ejemplo completo con valores reales:**

```hcl
region = "us-east-1"
key_name = "vockey"
admin_cidr = "186.81.58.137/32"

# RDS Password - Cambiar esto por tu contraseña segura
rds_password = "!QAZxsw2#EDC"
rds_instance_class = "db.t3.micro"

# Opcional
repo_branch = "develop"
```

> **⚠️ IMPORTANTE**: 
> - El archivo `terraform.tfvars` está en `.gitignore` y **NO se subirá al repositorio**
> - Usa una contraseña segura para RDS y guárdala en un gestor de contraseñas
> - Si cambias de red (WiFi diferente, VPN), actualiza `admin_cidr` con tu nueva IP
> - Si cambias de rama del repositorio, actualiza `repo_branch`

---

## 5) Terraform (carpeta `infra/`)

Entra a la carpeta `infra/` del proyecto y ejecuta:

### 5.1 Inicializar Terraform

```bash
cd infra
terraform init
terraform fmt -recursive
terraform validate
```

### 5.2 Plan y Apply

```bash
# Ver qué se va a crear (plan)
terraform plan -var-file=".\terraform.tfvars"

# Crear recursos (apply)
terraform apply -var-file=".\terraform.tfvars"

# Tener el destroy mas cerca
terraform destroy -var-file=".\terraform.tfvars"
```

**Tiempo estimado**: ~15-20 minutos
- RDS: ~10-15 minutos (lo que más tarda)
- EC2, S3, Security Groups: ~2-3 minutos

Cuando Terraform solicite confirmación, escribe `yes`.

### 5.3 Obtener outputs

Después de `terraform apply`, guarda los outputs:

```bash
terraform output -json > outputs.json

# O ver outputs específicos
terraform output alb_dns_name
terraform output rds_endpoints
terraform output s3_bucket_name
terraform output public_ips
```

**Outputs importantes:**
- `alb_dns_name` - DNS del Application Load Balancer (para acceder a la API)
- `rds_endpoints` - Endpoints de RDS (Core y Auth)
- `rds_addresses` - Direcciones IP/hostnames de RDS
- `s3_bucket_name` - Nombre del bucket S3
- `public_ips` - IPs públicas de las instancias EC2 (para SSH)

### 5.4 ¿Qué hacer con los outputs?

Los outputs de Terraform se usan automáticamente en el `user-data` de las instancias EC2. Sin embargo, puedes necesitarlos para:

**1. Actualizar colección de Postman** (ver sección 13):
- `alb_dns_name` → Actualizar `base_url` en el environment de Postman

**2. Verificación manual:**
- `rds_endpoints` → Verificar conexión desde instancias Core
- `s3_bucket_name` → Verificar que los videos se suben correctamente
- `public_ips` → SSH a las instancias para debugging

**3. Guardar para referencia:**
```bash
terraform output -json > outputs.json
# Útil para documentar qué valores se usaron en el despliegue
```

**4. Actualizar manualmente `.env` si es necesario:**
Si el user-data falla, puedes usar los outputs para crear manualmente el `.env` (ver sección 7, Modo B).

**Nota**: Si cambias algo y haces `terraform apply` nuevamente, los outputs se actualizarán automáticamente.

---

## 6) Validación rápida de recursos creados

### 6.1 Verificar instancias EC2

```bash
aws ec2 describe-instances   --filters "Name=tag:Project,Values=ANB" "Name=instance-state-name,Values=running"   --query 'Reservations[].Instances[].{Name:Tags[?Key==`Name`]|[0].Value,PublicIP:PublicIpAddress,PrivateIP:PrivateIpAddress}'   --output table
```

### 6.2 Verificar RDS

```bash
aws rds describe-db-instances \
  --filters "Name=tag:Project,Values=ANB" \
  --query 'DBInstances[].{Identifier:DBInstanceIdentifier,Status:DBInstanceStatus,Endpoint:Endpoint.Address}' \
  --output table
```

Deben estar en estado `"available"` antes de poder usarse (~10-15 minutos después del apply).

### 6.3 Verificar S3 Bucket

```bash
terraform output s3_bucket_name
aws s3 ls | grep anb-basketball-bucket
```

### 6.4 Verificar ALB

```bash
terraform output alb_dns_name
# Debe mostrar algo como: anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com
```

**Probar acceso al ALB:**
```bash
curl http://$(terraform output -raw alb_dns_name)/api/health
# Debe responder: {"status": "healthy"}
```

---

## 7) Despliegue de contenedores (multihost)

### Modo A — **Automático** (con `user-data`) - ✅ Recomendado

Si usaste el `user-data` provisto, cada instancia EC2 ya debe:
1. Instalar Docker/Compose
2. Clonar el repo en **`/opt/anb-cloud`** (rama especificada en `repo_branch`)
3. Generar `.env` automáticamente con:
   - **RDS endpoints** (si están configurados)
   - **S3 bucket** (si está configurado)
   - IPs de otras instancias (MQ, etc.)
4. Levantar servicios con Docker Compose según el `ROLE`

**El `user-data` configura automáticamente:**
- **Core**: Usa RDS endpoints si están disponibles, sino fallback a instancia DB local
- **Worker**: Configurado para usar S3 si `s3_bucket` está definido
- **Obs**: Configuración de Prometheus con IPs de otras instancias

**Verificar estado** (en cada instancia):

```bash
# SSH a la instancia
ssh -i ~/.ssh/vockey.pem ubuntu@<IP_PUBLICA>

# Verificar servicios
cd /opt/anb-cloud
docker compose -f docker-compose.multihost.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Ver logs
docker compose -f docker-compose.multihost.yml logs --tail=50 anb_api
```

**Verificar configuración (.env):**
```bash
# En instancia Core
cat /opt/anb-cloud/.env | grep -E "DB_URL|S3_BUCKET|STORAGE_BACKEND"
# Debe mostrar:
# DATABASE_URL=postgresql+asyncpg://anb_user:...@anb-core-rds.xxxxx.rds.amazonaws.com:5432/anb_core
# STORAGE_BACKEND=s3 (si S3 está configurado)
# S3_BUCKET=anb-basketball-bucket-xxxxx
```

### Modo B — **Manual**

Si necesitas hacer configuración manual o el user-data falla:

1. **SSH a cada instancia EC2**
   ```bash
   ssh -i ~/.ssh/vockey.pem ubuntu@<IP_PUBLICA_EC2>
   ```

2. **Clonar el repositorio** (si no está automático):
   ```bash
   cd /opt
   sudo git clone <repo_url> anb-cloud
   cd anb-cloud
   sudo git checkout <rama>  # Ej: develop, refactor-carga
   sudo chown -R ubuntu:ubuntu /opt/anb-cloud
   ```

3. **Obtener valores de Terraform** (desde tu PC local):
   ```bash
   cd infra
   terraform output rds_addresses
   terraform output s3_bucket_name
   terraform output alb_dns_name
   ```

4. **Crear `.env` manualmente** en `/opt/anb-cloud/.env`:

**Ejemplo completo de `.env` para instancia Core:**

```bash
# ========================================
# Archivo: /opt/anb-cloud/.env
# Instancia: Core (API + Auth Service)
# ========================================

# Aplicación
APP_ENV=production
ROLE=core

# Base de datos RDS (obtener desde: terraform output rds_addresses)
# Reemplazar anb-core-rds.xxxxx.us-east-1.rds.amazonaws.com con tu endpoint
DB_URL_CORE=postgresql+asyncpg://anb_user:TU_PASSWORD_RDS@anb-core-rds.xxxxx.us-east-1.rds.amazonaws.com:5432/anb_core
DB_URL_AUTH=postgresql+asyncpg://anb_user:TU_PASSWORD_RDS@anb-auth-rds.xxxxx.us-east-1.rds.amazonaws.com:5432/anb_auth

# PostgreSQL (solo si no usas RDS - fallback)
POSTGRES_USER=anb_user
POSTGRES_PASSWORD=anb_pass
POSTGRES_CORE_DB=anb_core
POSTGRES_AUTH_DB=anb_auth

# S3 Configuration (obtener desde: terraform output s3_bucket_name)
STORAGE_BACKEND=s3
S3_BUCKET=anb-basketball-bucket-xxxxx  # Reemplazar con tu bucket
S3_REGION=us-east-1
S3_PREFIX=uploads
S3_FORCE_PATH_STYLE=0
S3_VERIFY_SSL=1

# RabbitMQ (obtener IP privada desde: terraform output public_ips)
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/
RABBITMQ_URL=amqp://rabbit:rabbitpass@<MQ_IP_PRIVADA>:5672/%2F
RABBITMQ_HOST=<MQ_IP_PRIVADA>

# JWT & Security
ACCESS_TOKEN_SECRET_KEY=mi_clave_de_acceso_secreta
REFRESH_TOKEN_SECRET_KEY=mi_clave_de_refresh_secreta
TOKEN_EXPIRE=600
REFRESH_TOKEN_EXPIRE=600
JWT_SECRET=mi_secreto_super_seguro_para_jwt_tokens_2024
ALGORITHM=HS256

# Loki (obtener desde: terraform output alb_dns_name)
LOKI_URL=http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com/loki/api/v1/push

# Upstreams (IP privada de Core)
UPSTREAM_API=http://<CORE_IP_PRIVADA>:8000
UPSTREAM_AUTH=http://<CORE_IP_PRIVADA>:8001
```

**Ejemplo completo de `.env` para instancia Worker:**

```bash
# ========================================
# Archivo: /opt/anb-cloud/.env
# Instancia: Worker (Celery)
# ========================================

# Aplicación
APP_ENV=production
ROLE=worker

# S3 Configuration (mismo bucket que Core)
STORAGE_BACKEND=s3
S3_BUCKET=anb-basketball-bucket-xxxxx  # Reemplazar con tu bucket
S3_REGION=us-east-1
S3_PREFIX=uploads

# RabbitMQ
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/
RABBITMQ_URL=amqp://rabbit:rabbitpass@<MQ_IP_PRIVADA>:5672/%2F
RABBITMQ_HOST=<MQ_IP_PRIVADA>

# Base de datos (para actualizar estado de videos procesados)
DATABASE_URL=postgresql://anb_user:TU_PASSWORD_RDS@anb-core-rds.xxxxx.us-east-1.rds.amazonaws.com:5432/anb_core

# Celery
CELERY_BROKER_URL=${RABBITMQ_URL}
CELERY_RESULT_BACKEND=rpc://

# Loki
LOKI_URL=http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com/loki/api/v1/push
```

4. **Levantar servicios** con Docker Compose:
   ```bash
   cd /opt/anb-cloud
   docker compose -f docker-compose.multihost.yml --profile core up -d
   docker compose -f docker-compose.multihost.yml --profile worker up -d
   # etc.
   ```

> **Nota**: Los valores de RDS, S3 y ALB se obtienen desde los outputs de Terraform. Reemplaza los placeholders (`xxxxx`, `<MQ_IP_PRIVADA>`, etc.) con los valores reales.

---

## 8) Acceso a servicios

### URLs a través del ALB

Una vez que todo esté funcionando, accede a los servicios a través del ALB:

```bash
# Obtener DNS del ALB
ALB_DNS=$(terraform output -raw alb_dns_name)
echo $ALB_DNS
```

**Servicios disponibles:**
- **API Docs**: `http://$ALB_DNS/api/docs`
- **Auth Docs**: `http://$ALB_DNS/auth/docs`
- **API Health**: `http://$ALB_DNS/api/health`
- **Grafana**: `http://$ALB_DNS/grafana/` (admin/admin)
- **Prometheus**: `http://$ALB_DNS/prometheus/`
- **RabbitMQ UI**: `http://$ALB_DNS/rabbitmq/` (rabbit/rabbitpass)

### Verificar que los videos se suben a S3

1. Sube un video a través de la API
2. Ve a AWS Console → S3
3. Busca el bucket: `anb-basketball-bucket-xxxxx`
4. Debe haber:
   - Carpeta `uploads/` - Videos originales
   - Carpeta `processed/` - Videos procesados (después del worker)

---

## 13) Configuración de Postman para pruebas

Para probar la API en AWS, necesitas actualizar la colección de Postman con el DNS del ALB.

### 13.1 Obtener el DNS del ALB

```bash
cd infra
terraform output -raw alb_dns_name
# Salida ejemplo: anb-public-alb-1947189888.us-east-1.elb.amazonaws.com
```

### 13.2 Importar colección y environment de Postman

1. **Abrir Postman Desktop o Postman Web**

2. **Importar colección:**
   - Click en **Import** (botón superior izquierdo)
   - Selecciona el archivo: `collections/ANB_Basketball_API.postman_collection.json`
   - Click en **Import**

3. **Importar environment para AWS:**
   - Click en **Import** nuevamente
   - Selecciona el archivo: `collections/ANB_Basketball_API.postman_environment_AWS.json`
   - Click en **Import**

4. **Seleccionar environment:**
   - En el dropdown superior derecho de Postman, selecciona **"ANB Basketball API - AWS Environment"**

### 13.3 Actualizar `base_url` en el environment

**Opción A: Desde Postman UI (Recomendado)**

1. Click en el icono de **ojo** (👁️) en la esquina superior derecha de Postman
2. Selecciona **"ANB Basketball API - AWS Environment"** en la lista
3. Click en **Edit** (icono de lápiz)
4. Busca la variable `base_url`
5. Actualiza el valor con el DNS del ALB (obtenido en 13.1):
   ```
   http://anb-public-alb-1947189888.us-east-1.elb.amazonaws.com
   ```
6. Click en **Save**

**Opción B: Editar archivo JSON directamente**

1. Abre el archivo: `collections/ANB_Basketball_API.postman_environment_AWS.json`
2. Busca la variable `base_url`:
   ```json
   {
     "key": "base_url",
     "value": "http://anb-public-alb-1947189888.us-east-1.elb.amazonaws.com",
     "type": "default",
     "enabled": true
   }
   ```
3. Reemplaza el valor con tu DNS del ALB (con `http://`)
4. Guarda el archivo
5. En Postman: **Environments** → Click en **"..."** (tres puntos) → **Reload** o re-importa el archivo

### 13.4 Probar la API

1. **Probar health check primero:**
   - Abre el request `GET /api/health`
   - Click en **Send**
   - Debe responder: `{"status": "healthy"}`

2. **Ejecutar flujo completo:**
   - `POST /auth/api/v1/signup` - Registrar usuario
   - `POST /auth/api/v1/login` - Iniciar sesión (guarda automáticamente `access_token`)
   - `POST /api/videos/upload` - Subir video (selecciona un archivo .mp4)
   - `GET /api/videos` - Listar mis videos

### 13.5 Notas importantes

- **Tokens**: Los tokens (`access_token`, `refresh_token`) se guardan automáticamente en el environment después de login
- **Video file**: Para subir videos, necesitas seleccionar un archivo `.mp4` en el request `POST /api/videos/upload` (Body → form-data → `video_file`)
- **Environment local vs AWS**: Usa `ANB_Basketball_API.postman_environment.json` para local y `ANB_Basketball_API.postman_environment_AWS.json` para AWS

> **Más información**: Consulta `collections/README.md` para detalles adicionales sobre la colección y tests automatizados.

---

## 9) Observabilidad
- **Promtail** usa `${LOKI_URL}` y el compose ya tiene `-config.expand-env=true`.
- **Prometheus**: ajusta `observability/prometheus/prometheus.yml` con las IPs/puertos:

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: nginx
    static_configs:
      - targets: ["${WEB_IP}:9113"]
  - job_name: cadvisor
    static_configs:
      - targets:
          - "${WEB_IP}:8080"
          - "${CORE_IP}:8080"
          - "${DB_IP}:8080"
          - "${MQ_IP}:8080"
          - "${WORKER_IP}:8080"
  - job_name: postgres
    static_configs:
      - targets:
          - "${DB_IP}:9187"    # postgres-exporter (core)
          - "${DB_IP}:9188"    # postgres-exporter (auth) - si aplica
```

> **Grafana**: por defecto suele ser `admin / admin` (a menos que lo sobrescribas en el compose).

---

## 10) Limpieza

**⚠️ IMPORTANTE**: RDS genera costos mientras esté activo. Elimínalo cuando no lo necesites.

```bash
cd infra
terraform destroy -var-file=terraform.tfvars

terraform destroy -var-file=".\terraform.tfvars"
```

Cuando Terraform solicite confirmación, revisa qué se va a destruir y escribe `yes`.

**Nota**: Si solo quieres detener las instancias EC2 sin destruir RDS:
```bash
# Detener instancias EC2 (no destruir)
aws ec2 stop-instances --instance-ids $(terraform output -json public_ips | jq -r '.[]' | xargs -I {} aws ec2 describe-instances --filters "Name=ip-address,Values={}" --query 'Reservations[0].Instances[0].InstanceId' --output text)
```

Pero para evitar costos de RDS, es mejor destruir todo con `terraform destroy`.

---

## 11) Notas y buenas prácticas

### Seguridad
- Mantén `admin_cidr` con tu IP `/32` (no expongas UIs a Internet)
- **Nunca** subas `terraform.tfvars` al repositorio (contiene contraseñas)
- Rota la contraseña de RDS periódicamente si es necesario
- Las credenciales de sesión temporal expiran; obtén nuevas desde AWS Academy Lab

### Costos
- **RDS genera costos continuos**: Elimínalo cuando no lo necesites (`terraform destroy`)
- Detén las instancias EC2 cuando no las uses: `aws ec2 stop-instances --instance-ids <id>`
- Revisa tu presupuesto en AWS Academy Lab

### Permisos
- Si tu rol en el lab **no** permite `ec2:RunInstances` o `rds:CreateDBInstance`, consulta al instructor
- Verifica que el **LabRole** tenga permisos S3 (necesario para que Worker suba videos)
- Para verificar permisos: AWS Console → IAM → Roles → LabRole → Permissions

### Compatibilidad
- Asegura que **todas las instancias** puedan resolver/alcanzar las IPs privadas configuradas
- Verifica que las instancias EC2 puedan conectarse a RDS (security group `rds` debe permitir tráfico desde `core` y `worker`)
- Si usas S3, verifica que las instancias Core y Worker tengan permisos IAM (LabRole)

---

## 12) Troubleshooting

### Problemas con RDS

**Error: "Cannot find version X.X for postgres"**
- **Solución**: Deja `engine_version` sin especificar en `main.tf` (AWS usará la versión predeterminada disponible)

**Error: "InvalidPermission.Duplicate" en security group**
- **Solución**: Las reglas de ingress para RDS ya existen de un intento anterior. Están comentadas en `main.tf` líneas 345-371. Las reglas ya funcionan, solo no están gestionadas por Terraform.

**RDS tarda mucho en crearse**
- **Normal**: RDS tarda ~10-15 minutos en estar disponible. Espera a que el estado sea `"available"`.

**No puedo conectar a RDS desde Core**
- Verifica que el security group `rds` permita tráfico desde el security group `core` en puerto 5432
- Verifica que los endpoints de RDS estén correctos en el `.env` de la instancia Core
- Verifica que la contraseña de RDS sea correcta

### Problemas con S3

**Videos no se suben a S3**
- Verifica que `STORAGE_BACKEND=s3` en el `.env` de Core
- Verifica que `S3_BUCKET` esté configurado correctamente
- Verifica permisos IAM: AWS Console → IAM → Roles → LabRole → Debe tener permisos `s3:PutObject`, `s3:GetObject`

**Worker no puede leer/escribir en S3**
- Verifica que el Worker tenga `S3_BUCKET` y `S3_REGION` en su `.env`
- Verifica que `boto3` esté instalado en el contenedor Worker (`worker/requirements.txt`)

### Problemas con ALB

**502 Bad Gateway desde ALB**
- Verifica que las instancias Core estén corriendo: `docker compose ps` en instancia Core
- Verifica que los servicios respondan en puertos 8000 (API) y 8001 (Auth)
- Verifica que el Target Group del ALB tenga las instancias Core registradas y "healthy"

**Health checks fallan**
- Verifica que `/api/health` y `/auth/api/v1/status` respondan sin autenticación
- Verifica logs de Core: `docker compose logs anb_api --tail=50`

**Ruta del compose**
- Asegúrate de ejecutar desde `/opt/anb-cloud`:
  ```bash
  cd /opt/anb-cloud
  test -f deploy/compose/docker-compose.multihost.yml || echo "No existe el compose en esa ruta"
  ```
- Valida sintaxis/servicios:
  ```bash
  docker compose -f deploy/compose/docker-compose.multihost.yml config --services
  ```

**Perfiles vs servicios**
- Si el compose **no** define el profile `db` (o similar), usa servicios concretos:  
  `docker compose -f ... up -d db`  
- Lista perfiles disponibles:
  ```bash
  docker compose -f deploy/compose/docker-compose.multihost.yml config --profiles
  ```

**Contenedores/health**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
for id in $(docker compose -f deploy/compose/docker-compose.multihost.yml ps -q); do
  echo "$(docker inspect -f '{{.Name}} -> {{.State.Status}} / {{if .State.Health}}{{.State.Health.Status}}{{end}}' $id)"
done
```

**Puertos publicados**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml port web 443 || true
docker compose -f deploy/compose/docker-compose.multihost.yml port grafana 3000 || true
```

**Logs rápidos**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml logs -n 200 web core db mq worker grafana prometheus loki
```

**Permisos Docker**
- Si tu usuario no puede usar Docker sin `sudo`, agrega al grupo:
  ```bash
  sudo usermod -aG docker $USER && newgrp docker
  ```

