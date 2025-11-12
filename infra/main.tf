terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws      = { source = "hashicorp/aws", version = "~> 5.0" }
    local    = { source = "hashicorp/local", version = "~> 2.5" }
    null     = { source = "hashicorp/null", version = "~> 3.2" }
    random   = { source = "hashicorp/random", version = "~> 3.6" }
    external = { source = "hashicorp/external", version = "~> 2.3" }
  }
}

# ========== Variables ==========
variable "region" {
  type    = string
  default = "us-east-1"
}
## Credenciales AWS para S3 (opcionalmente definir vía TF_VAR_*)
variable "key_name" {
  type        = string
  description = "Nombre de Key Pair existente (p.ej. 'vockey' en AWS Academy). Vacío = sin SSH."
  default     = "vockey"
}

# Repo / compose multihost
variable "repo_url" {
  type    = string
  default = "https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube.git"
}
variable "repo_branch" {
  type    = string
  default = "develop"
}
variable "compose_file" {
  type    = string
  default = "/opt/anb-cloud/docker-compose.multihost.yml"
}

# Acceso a UIs (no abrimos SSH: puerto 22 no disponible en el lab)
variable "admin_cidr" {
  type        = string
  description = "CIDR permitido para UIs (ej: 186.80.29.7/32)."
  default     = "0.0.0.0/0"
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0))
    error_message = "admin_cidr debe ser un CIDR válido, ej: 1.2.3.4/32."
  }
}

# AMI fija (opcional)
variable "ami_id" {
  type    = string
  default = ""
}

# AZ preferida (evita us-east-1e por compatibilidad)
variable "az_name" {
  type        = string
  description = "AZ preferida (ej: us-east-1a). Si no existe, se usa la primera subred del VPC."
  default     = "us-east-1a"
}

# RDS PostgreSQL
variable "rds_password" {
  type        = string
  description = "Password para RDS PostgreSQL (usar terraform.tfvars o variable de entorno TF_VAR_rds_password)"
  sensitive   = true
  default     = ""
}

variable "rds_instance_class" {
  type        = string
  description = "Instance class para RDS (db.t3.micro, db.t3.small)"
  default     = "db.t3.micro"
}

# Assets del worker (opcional): rutas locales para subir a S3 y claves destino
variable "assets_inout_path" {
  type        = string
  description = "Ruta local del archivo de intro/outro a subir a S3 (obligatorio). Por defecto apunta a ../worker/assets/inout.mp4 desde la carpeta infra."
  default     = "../worker/assets/inout.mp4"
  validation {
    condition     = length(var.assets_inout_path) > 0
    error_message = "Debe proporcionar assets_inout_path (ruta local del archivo de intro/outro)."
  }
}

variable "assets_wm_path" {
  type        = string
  description = "Ruta local del archivo de watermark a subir a S3 (obligatorio). Por defecto apunta a ../worker/assets/watermark.png desde la carpeta infra."
  default     = "../worker/assets/watermark.png"
  validation {
    condition     = length(var.assets_wm_path) > 0
    error_message = "Debe proporcionar assets_wm_path (ruta local del archivo de watermark)."
  }
}

variable "assets_inout_key" {
  type        = string
  description = "Clave (key) en S3 para el asset de intro/outro."
  default     = "assets/inout.mp4"
}

variable "assets_wm_key" {
  type        = string
  description = "Clave (key) en S3 para el asset de watermark."
  default     = "assets/watermark.png"
}

variable "aws_profile" {
  type    = string
  default = ""
}

# Tipos por rol (compatibles con el lab)
variable "instance_type_web" {
  type    = string
  default = "t3.small"
}
variable "instance_type_core" {
  type    = string
  default = "t3.small"
}
variable "instance_type_auth" {
  type    = string
  default = "t3.small"
}
variable "instance_type_worker" {
  type    = string
  default = "t3.large"
}
variable "instance_type_obs" {
  type    = string
  default = "t3.small"
}

# ========== Leer credenciales AWS desde variables de entorno del host que ejecuta Terraform ==========
# Utilizar un perfir permite ser agnotico al sistema operativo utilizado para ejecutar terraform
provider "aws" {
  region  = var.region
  profile = var.aws_profile != "" ? var.aws_profile : null
}

# SQS (Celery broker) variables
## SQS settings are derived from provisioned resources (no manual variables)

# Detectar sistema operativo del host que ejecuta Terraform (Windows vs Unix)
locals {
  # Detectar Windows por presencia del PowerShell clásico
  is_windows = fileexists("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
}

# Leer credenciales AWS desde variables de entorno del host (cross-platform)
# - En Windows usa PowerShell clásico
# - En macOS/Linux usa bash
data "external" "aws_env_win" {
  count = local.is_windows ? 1 : 0
  program = [
    "powershell.exe",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    "Write-Output ((@{ aws_access_key_id = $Env:AWS_ACCESS_KEY_ID; aws_secret_access_key = $Env:AWS_SECRET_ACCESS_KEY; aws_session_token = $Env:AWS_SESSION_TOKEN; aws_region = $Env:AWS_REGION } | ConvertTo-Json -Compress))"
  ]
}

data "external" "aws_env_unix" {
  count = local.is_windows ? 0 : 1
  program = [
    "bash",
    "-lc",
    "printf '{\"aws_access_key_id\":\"%s\",\"aws_secret_access_key\":\"%s\",\"aws_session_token\":\"%s\",\"aws_region\":\"%s\"}\\n' \"$${AWS_ACCESS_KEY_ID:-}\" \"$${AWS_SECRET_ACCESS_KEY:-}\" \"$${AWS_SESSION_TOKEN:-}\" \"$${AWS_REGION:-${var.region}}\""
  ]
}

locals {
  # Unificar salida en un solo mapa accesible como local.aws_env
  aws_env = local.is_windows ? data.external.aws_env_win[0].result : data.external.aws_env_unix[0].result
}

# ========== VPC/Subred por defecto ==========
data "aws_vpc" "default" { default = true }

# Todas las subredes del VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Subredes en la AZ preferida
data "aws_subnets" "az" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "availability-zone"
    values = [var.az_name]
  }
}

# Ubuntu 22.04 (Canonical)
data "aws_ami" "ubuntu22" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

locals {
  subnet_id = length(data.aws_subnets.az.ids) > 0 ? element(data.aws_subnets.az.ids, 0) : element(data.aws_subnets.default.ids, 0)
  ami_id    = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu22.id
  tags_base = { Project = "ANB", Environment = "lab" }
}

# ========== Security Groups ==========
# Con reglas de egress explícitas para permitir conectividad a internet

# ALB público (HTTP 80)
resource "aws_security_group" "alb" {
  name        = "anb-alb-sg"
  description = "Public ALB"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "alb_http_in" {
  type              = "ingress"
  security_group_id = aws_security_group.alb.id
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "alb_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.alb.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# CORE: 8000 (API), 8001 (Auth) solo desde WEB
resource "aws_security_group" "core" {
  name        = "anb-core-sg"
  description = "CORE ingress from VPC (for internal LB)"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "core_from_alb_8000" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}
## Auth will move to its own SG; remove ALB->8001 on CORE

# Allow Prometheus (OBS) to scrape CORE metrics (API 8000, Auth 8001) and cadvisor (8080)
resource "aws_security_group_rule" "core_from_obs_8000" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
## Auth will move to its own SG; remove OBS->8001 on CORE
resource "aws_security_group_rule" "core_from_obs_8080" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

# Reglas de egress para CORE (acceso a internet)
resource "aws_security_group_rule" "core_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.core.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "core_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.core.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group" "worker" {
  name        = "anb-worker-sg"
  description = "WORKER"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

# AUTH: 8001 (Auth app) desde ALB/CORE/OBS y 8080 (cAdvisor) desde OBS
resource "aws_security_group" "auth" {
  name        = "anb-auth-sg"
  description = "AUTH ingress from ALB/CORE and OBS"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "auth_from_alb_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.auth.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "auth_from_core_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.auth.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
}

resource "aws_security_group_rule" "auth_from_obs_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.auth.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

resource "aws_security_group_rule" "auth_from_obs_8080" {
  type                     = "ingress"
  security_group_id        = aws_security_group.auth.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

resource "aws_security_group_rule" "auth_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.auth.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

resource "aws_security_group_rule" "auth_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.auth.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "auth_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.auth.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# RDS: Security group para bases de datos RDS
resource "aws_security_group" "rds" {
  name        = "anb-rds-sg"
  description = "RDS PostgreSQL ingress from CORE & WORKER"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

# Reglas de ingress para RDS (desde CORE y WORKER)
# Necesarias para que las apps (API/Auth/Worker) en EC2 puedan conectarse a RDS.
resource "aws_security_group_rule" "rds_ingress_from_core" {
  type                     = "ingress"
  security_group_id        = aws_security_group.rds.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
  description              = "Core/API to RDS"
}

resource "aws_security_group_rule" "rds_ingress_from_auth" {
  type                     = "ingress"
  security_group_id        = aws_security_group.rds.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.auth.id
  description              = "Auth service to RDS"
}

resource "aws_security_group_rule" "rds_ingress_from_worker" {
  type                     = "ingress"
  security_group_id        = aws_security_group.rds.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.worker.id
  description              = "Worker to RDS"
}

# Permitir acceso directo desde la IP administradora (solo 5432)
resource "aws_security_group_rule" "rds_ingress_from_admin" {
  type              = "ingress"
  security_group_id = aws_security_group.rds.id
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
  description       = "Admin IP to RDS"
}

# Reglas de egress para RDS (acceso a internet)
resource "aws_security_group_rule" "rds_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.rds.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "rds_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.rds.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# Reglas de egress para WORKER (acceso a internet)
resource "aws_security_group_rule" "worker_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.worker.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# ========== RDS Subnet Group ==========
# RDS requiere un subnet group con subnets en al menos 2 AZs diferentes
resource "aws_db_subnet_group" "anb_rds" {
  name       = "anb-rds-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = merge(local.tags_base, {
    Name = "anb-rds-subnet-group"
  })
}

resource "aws_security_group_rule" "worker_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.worker.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}


# OBS: 9090, 3000, 3100 solo admin
resource "aws_security_group" "obs" {
  name        = "anb-obs-sg"
  description = "Observability UIs"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}
resource "aws_security_group_rule" "obs_prom" {
  type              = "ingress"
  security_group_id = aws_security_group.obs.id
  from_port         = 9090
  to_port           = 9090
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}
resource "aws_security_group_rule" "obs_graf" {
  type              = "ingress"
  security_group_id = aws_security_group.obs.id
  from_port         = 3000
  to_port           = 3000
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

resource "aws_security_group_rule" "obs_from_alb_3000" {
  type                     = "ingress"
  security_group_id        = aws_security_group.obs.id
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}
resource "aws_security_group_rule" "obs_from_alb_9090" {
  type                     = "ingress"
  security_group_id        = aws_security_group.obs.id
  from_port                = 9090
  to_port                  = 9090
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}
resource "aws_security_group_rule" "obs_from_alb_3100" {
  type                     = "ingress"
  security_group_id        = aws_security_group.obs.id
  from_port                = 3100
  to_port                  = 3100
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}
resource "aws_security_group_rule" "obs_loki" {
  type              = "ingress"
  security_group_id = aws_security_group.obs.id
  from_port         = 3100
  to_port           = 3100
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

# Allow OTLP HTTP (4318) to Tempo from CORE and WORKER
resource "aws_security_group_rule" "obs_otlp_from_core" {
  type                     = "ingress"
  security_group_id        = aws_security_group.obs.id
  from_port                = 4318
  to_port                  = 4318
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
  description              = "Allow OTLP HTTP traces from CORE"
}

resource "aws_security_group_rule" "obs_otlp_from_worker" {
  type                     = "ingress"
  security_group_id        = aws_security_group.obs.id
  from_port                = 4318
  to_port                  = 4318
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.worker.id
  description              = "Allow OTLP HTTP traces from WORKER"
}

# Reglas de egress para OBS (acceso a internet)
resource "aws_security_group_rule" "obs_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.obs.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "obs_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.obs.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# SSH: habilitar acceso 22/TCP para troubleshooting desde admin_cidr en TODOS los roles


resource "aws_security_group_rule" "core_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.core.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}


resource "aws_security_group_rule" "worker_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.worker.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

# Allow Prometheus (OBS) to scrape cadvisor on WORKER
resource "aws_security_group_rule" "worker_from_obs_8080" {
  type                     = "ingress"
  security_group_id        = aws_security_group.worker.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

# Allow Prometheus (OBS) to scrape WORKER metrics exporter (9100)
resource "aws_security_group_rule" "worker_from_obs_9100" {
  type                     = "ingress"
  security_group_id        = aws_security_group.worker.id
  from_port                = 9100
  to_port                  = 9100
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

resource "aws_security_group_rule" "obs_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.obs.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

# ========== EC2 por rol con user-data (templatefile) ==========
# Orden sin ciclos:
#   CORE usa AutoScalingGroup (depende de RDS)
#   WORKER no depende de MQ
#   WEB depende de CORE
#   OBS no depende de otros (Prometheus se puede configurar luego)

## CORE ahora se gestiona con Launch Template + AutoScalingGroup

resource "aws_launch_template" "core_lt" {
  name_prefix   = "anb-core-lt-"
  image_id      = local.ami_id
  instance_type = var.instance_type_core
  key_name      = var.key_name == "" ? null : var.key_name

  vpc_security_group_ids = [aws_security_group.core.id]

  # Métricas detalladas de EC2 a 1 minuto para reacciones más rápidas
  monitoring {
    enabled = true
  }

  user_data = base64encode(templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "core",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    worker_ip         = "",
    obs_ip            = "",
    auth_ip           = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = aws_db_instance.core.address,
    rds_auth_endpoint = aws_db_instance.auth.address,
    rds_password      = var.rds_password != "" ? var.rds_password : "anb_pass_change_me",
    s3_bucket         = aws_s3_bucket.anb_videos.bucket,
    assets_inout_key  = "",
    assets_wm_key     = "",
    # Broker SQS sin parámetros en la URL; región va en AWS_REGION y transport options
    sqs_broker_url        = "sqs://",
    sqs_queue_name        = aws_sqs_queue.video_tasks.name,
    aws_region            = try(local.aws_env.aws_region, var.region),
    aws_profile           = var.aws_profile,
    aws_access_key_id     = try(local.aws_env.aws_access_key_id, ""),
    aws_secret_access_key = try(local.aws_env.aws_secret_access_key, ""),
    aws_session_token     = try(local.aws_env.aws_session_token, "")
  }))

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 40
      volume_type = "gp3"
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(local.tags_base, { Name = "anb-core", Role = "core" })
  }

  tag_specifications {
    resource_type = "volume"
    tags          = local.tags_base
  }
}

resource "aws_autoscaling_group" "core" {
  name                      = "anb-core-asg"
  desired_capacity          = 1
  min_size                  = 1
  max_size                  = 3
  vpc_zone_identifier       = [local.subnet_id]
  health_check_type         = "ELB"
  health_check_grace_period = 120
  # Reducir tiempo entre decisiones del ASG y warmup para TargetTracking
  default_cooldown        = 120
  default_instance_warmup = 120

  # Publicar métricas del grupo a 1 minuto para mejor visibilidad
  metrics_granularity = "1Minute"
  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupPendingInstances",
    "GroupStandbyInstances",
    "GroupTerminatingInstances",
    "GroupTotalInstances"
  ]
  target_group_arns = [aws_lb_target_group.tg_api.arn]

  launch_template {
    id      = aws_launch_template.core_lt.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "anb-core"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_db_instance.core, aws_db_instance.auth, aws_s3_bucket.anb_videos]
}

resource "aws_autoscaling_policy" "core_cpu_target" {
  name                   = "anb-core-cpu-60"
  autoscaling_group_name = aws_autoscaling_group.core.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value     = 60
    disable_scale_in = false
  }
}

resource "aws_instance" "auth" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_auth
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.auth.id]
  depends_on                  = [aws_db_instance.auth, aws_s3_bucket.anb_videos]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "auth",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    worker_ip         = "",
    obs_ip            = "",
    auth_ip           = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = aws_db_instance.core.address,
    rds_auth_endpoint = aws_db_instance.auth.address,
    rds_password      = var.rds_password != "" ? var.rds_password : "anb_pass_change_me",
    s3_bucket         = aws_s3_bucket.anb_videos.bucket,
    assets_inout_key  = "",
    assets_wm_key     = "",
    # Auth no usa la cola, pero el template requiere estas claves; dejamos valores vacíos
    sqs_broker_url        = "",
    sqs_queue_name        = "",
    aws_region            = try(local.aws_env.aws_region, var.region),
    aws_profile           = var.aws_profile,
    aws_access_key_id     = try(local.aws_env.aws_access_key_id, ""),
    aws_secret_access_key = try(local.aws_env.aws_secret_access_key, ""),
    aws_session_token     = try(local.aws_env.aws_session_token, "")
  })
  tags = merge(local.tags_base, { Name = "anb-auth" })
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
}

resource "aws_instance" "worker" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_worker
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.worker.id]
  depends_on                  = [aws_s3_bucket.anb_videos, aws_s3_object.asset_inout, aws_s3_object.asset_wm]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role                  = "worker",
    repo_url              = var.repo_url,
    repo_branch           = var.repo_branch,
    compose_file          = var.compose_file,
    web_ip                = "",
    core_ip               = "",
    worker_ip             = "",
    obs_ip                = "",
    auth_ip               = "",
    alb_dns               = aws_lb.public.dns_name,
    rds_core_endpoint     = aws_db_instance.core.address,
    rds_auth_endpoint     = "",
    rds_password          = var.rds_password,
    s3_bucket             = aws_s3_bucket.anb_videos.bucket, # Worker necesita S3 para leer videos
    assets_inout_key      = var.assets_inout_key,
    assets_wm_key         = var.assets_wm_key,
    sqs_broker_url        = "sqs://",
    sqs_queue_name        = aws_sqs_queue.video_tasks.name,
    aws_region            = try(local.aws_env.aws_region, var.region),
    aws_profile           = var.aws_profile,
    aws_access_key_id     = try(local.aws_env.aws_access_key_id, ""),
    aws_secret_access_key = try(local.aws_env.aws_secret_access_key, ""),
    aws_session_token     = try(local.aws_env.aws_session_token, "")
  })
  tags = merge(local.tags_base, { Name = "anb-worker" })
  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }
}

resource "aws_instance" "obs" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_obs
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.obs.id]
  # Obs SIN dependencias para evitar ciclos. Prometheus se ajusta luego si hace falta.
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role                  = "obs",
    repo_url              = var.repo_url,
    repo_branch           = var.repo_branch,
    compose_file          = var.compose_file,
    web_ip                = "",
    core_ip               = "",
    auth_ip               = aws_instance.auth.private_ip,
    worker_ip             = aws_instance.worker.private_ip,
    obs_ip                = "",
    alb_dns               = aws_lb.public.dns_name,
    rds_core_endpoint     = aws_db_instance.core.address,
    rds_auth_endpoint     = aws_db_instance.auth.address,
    rds_password          = var.rds_password,
    s3_bucket             = aws_s3_bucket.anb_videos.bucket,
    assets_inout_key      = "",
    assets_wm_key         = "",
    sqs_broker_url        = "sqs://",
    sqs_queue_name        = aws_sqs_queue.video_tasks.name,
    aws_region            = try(local.aws_env.aws_region, var.region),
    aws_profile           = var.aws_profile,
    aws_access_key_id     = try(local.aws_env.aws_access_key_id, ""),
    aws_secret_access_key = try(local.aws_env.aws_secret_access_key, ""),
    aws_session_token     = try(local.aws_env.aws_session_token, "")
  })
  tags = merge(local.tags_base, { Name = "anb-obs" })
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
}

# ========== RDS PostgreSQL ==========
resource "aws_db_instance" "core" {
  identifier = "anb-core-rds"
  engine     = "postgres"
  # engine_version omitido - AWS usará la versión predeterminada disponible para postgres
  instance_class        = var.rds_instance_class
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "anb_core"
  username = "anb_user"
  password = var.rds_password != "" ? var.rds_password : "anb_pass_change_me"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.anb_rds.name
  publicly_accessible    = true

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  skip_final_snapshot = true
  deletion_protection = false

  tags = merge(local.tags_base, { Name = "anb-core-rds" })
}

resource "aws_db_instance" "auth" {
  identifier = "anb-auth-rds"
  engine     = "postgres"
  # engine_version omitido - AWS usará la versión predeterminada disponible para postgres
  instance_class        = var.rds_instance_class
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "anb_auth"
  username = "anb_user"
  password = var.rds_password != "" ? var.rds_password : "anb_pass_change_me"

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.anb_rds.name
  publicly_accessible    = true

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  skip_final_snapshot = true
  deletion_protection = false

  tags = merge(local.tags_base, { Name = "anb-auth-rds" })
}

# ========== S3 Bucket ==========
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "anb_videos" {
  bucket = "anb-basketball-bucket-${random_id.bucket_suffix.hex}"
  # Elimina el bucket aunque tenga objetos y versiones (provider aws >= 5)
  force_destroy = true
  tags          = local.tags_base
}

resource "aws_s3_bucket_versioning" "anb_videos" {
  bucket = aws_s3_bucket.anb_videos.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "anb_videos" {
  bucket = aws_s3_bucket.anb_videos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "anb_videos" {
  bucket = aws_s3_bucket.anb_videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Objetos S3 opcionales: subir assets del worker si se proporcionan rutas locales
resource "aws_s3_object" "asset_inout" {
  bucket = aws_s3_bucket.anb_videos.bucket
  key    = var.assets_inout_key
  source = abspath("${path.module}/${var.assets_inout_path}")
  etag   = filemd5(abspath("${path.module}/${var.assets_inout_path}"))
}

resource "aws_s3_object" "asset_wm" {
  bucket = aws_s3_bucket.anb_videos.bucket
  key    = var.assets_wm_key
  source = abspath("${path.module}/${var.assets_wm_path}")
  etag   = filemd5(abspath("${path.module}/${var.assets_wm_path}"))
}

# ========== SQS (Celery broker) ==========
resource "aws_sqs_queue" "video_dlq" {
  name                      = "video_dlq"
  message_retention_seconds = 1209600 # 14 días
}

resource "aws_sqs_queue" "video_tasks" {
  name                       = "video_tasks"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600 # 14 días
  receive_wait_time_seconds  = 20      # long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.video_dlq.arn
    maxReceiveCount     = 5
  })
}

# ========== Application Load Balancer ==========
resource "aws_lb" "public" {
  name               = "anb-public-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
  idle_timeout       = 60
  enable_http2       = true
  tags               = local.tags_base
}

# Target groups (puertos según upstreams de Nginx)
resource "aws_lb_target_group" "tg_api" {
  name        = "anb-tg-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path                = "/health"
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    timeout             = 5
  }
  tags = local.tags_base
}

resource "aws_lb_target_group" "tg_auth" {
  name        = "anb-tg-auth"
  port        = 8001
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path                = "/auth/api/v1/status"
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    timeout             = 5
  }
  tags = local.tags_base
}


resource "aws_lb_target_group" "tg_grafana" {
  name        = "anb-tg-grafana"
  port        = 3000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path    = "/api/health"
    matcher = "200-399"
  }
  tags = local.tags_base
}

resource "aws_lb_target_group" "tg_prom" {
  name        = "anb-tg-prom"
  port        = 9090
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path    = "/-/ready"
    matcher = "200-399"
  }
  tags = local.tags_base
}

resource "aws_lb_target_group" "tg_loki" {
  name        = "anb-tg-loki"
  port        = 3100
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path    = "/ready"
    matcher = "200-399"
  }
  tags = local.tags_base
}

## NOTE: URL rewrite transforms are applied via AWS CLI using local/NULL providers
## to keep apps at root and strip prefixes at the ALB level.

# Listener HTTP 80 (default 404)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.public.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "not found"
      status_code  = "404"
    }
  }
}

# Reglas de ruteo (equivalentes a nginx.conf)
resource "aws_lb_listener_rule" "r_api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_api.arn
  }
  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

resource "aws_lb_listener_rule" "r_openapi_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 11
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/api/openapi.json"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/openapi.json"]
    }
  }
}

resource "aws_lb_listener_rule" "r_docs_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 12
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/api/docs/oauth2-redirect"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/docs/oauth2-redirect"]
    }
  }
}

resource "aws_lb_listener_rule" "r_auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_auth.arn
  }
  condition {
    path_pattern {
      values = ["/auth/*"]
    }
  }
}


resource "aws_lb_listener_rule" "r_grafana_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 40
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/grafana/"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/grafana"]
    }
  }
}

resource "aws_lb_listener_rule" "r_grafana" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 41
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_grafana.arn
  }
  condition {
    path_pattern {
      values = ["/grafana/*"]
    }
  }
}

resource "aws_lb_listener_rule" "r_prom_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 50
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/prometheus/"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/prometheus"]
    }
  }
}

resource "aws_lb_listener_rule" "r_prom" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 51
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_prom.arn
  }
  condition {
    path_pattern {
      values = ["/prometheus/*"]
    }
  }
}

resource "aws_lb_listener_rule" "r_loki_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 60
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/loki/"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/loki"]
    }
  }
}

resource "aws_lb_listener_rule" "r_loki" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 61
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_loki.arn
  }
  condition {
    path_pattern {
      values = ["/loki/*"]
    }
  }
}

resource "aws_lb_listener_rule" "r_health_fixed" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 90
  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "ok"
      status_code  = "200"
    }
  }
  condition {
    path_pattern {
      values = ["/nginx-health"]
    }
  }
}

# Registro de instancias en los target groups
## Registro dinámico de CORE al TG via AutoScalingGroup (se quita attachment estático)

resource "aws_lb_target_group_attachment" "att_auth_auth" {
  target_group_arn = aws_lb_target_group.tg_auth.arn
  target_id        = aws_instance.auth.id
}


resource "aws_lb_target_group_attachment" "att_grafana_obs" {
  target_group_arn = aws_lb_target_group.tg_grafana.arn
  target_id        = aws_instance.obs.id
}

resource "aws_lb_target_group_attachment" "att_prom_obs" {
  target_group_arn = aws_lb_target_group.tg_prom.arn
  target_id        = aws_instance.obs.id
}

resource "aws_lb_target_group_attachment" "att_loki_obs" {
  target_group_arn = aws_lb_target_group.tg_loki.arn
  target_id        = aws_instance.obs.id
}

# ========== ALB URL Rewrites (strip /grafana and /prometheus prefixes) ==========
# Terraform AWS provider may not expose rule transforms yet; apply via AWS CLI.
# Requires AWS CLI available where Terraform runs.

resource "local_file" "alb_transform_grafana" {
  filename = "${path.module}/alb_transform_grafana.json"
  # Do not rewrite Grafana paths; Grafana is configured to serve from /grafana
  content = jsonencode([])
}

# Provide the existing actions for the Grafana rule so modify-rule has a valid update
resource "local_file" "alb_actions_grafana" {
  filename = "${path.module}/alb_actions_grafana.json"
  content = jsonencode([
    {
      Type = "forward",
      ForwardConfig = {
        TargetGroups = [
          { TargetGroupArn = aws_lb_target_group.tg_grafana.arn, Weight = 1 }
        ]
      }
    }
  ])
}

resource "local_file" "alb_transform_prom" {
  filename = "${path.module}/alb_transform_prom.json"
  content = jsonencode([
    {
      Type = "url-rewrite",
      UrlRewriteConfig = {
        Rewrites = [{ Regex = "^/prometheus(.*)$", Replace = "$1" }]
      }
    }
  ])
}

resource "null_resource" "alb_apply_transform_grafana" {
  depends_on = [aws_lb_listener_rule.r_grafana, local_file.alb_transform_grafana, local_file.alb_actions_grafana]
  triggers = {
    rule_arn = aws_lb_listener_rule.r_grafana.arn
    # Hash the intended content instead of the file, since the file doesn't exist yet at plan time
    transform = sha1(local_file.alb_transform_grafana.content)
    actions   = sha1(local_file.alb_actions_grafana.content)
  }

  provisioner "local-exec" {
    command = "aws elbv2 modify-rule --region ${var.region} --rule-arn ${aws_lb_listener_rule.r_grafana.arn} --actions file://${replace(path.module, "\\", "/")}/alb_actions_grafana.json --transforms file://${replace(path.module, "\\", "/")}/alb_transform_grafana.json"
    environment = merge(
      {
        AWS_REGION         = var.region
        AWS_DEFAULT_REGION = var.region
      },
      var.aws_profile != "" ? { AWS_PROFILE = var.aws_profile } : {},
      {
        AWS_ACCESS_KEY_ID     = try(local.aws_env.aws_access_key_id, "")
        AWS_SECRET_ACCESS_KEY = try(local.aws_env.aws_secret_access_key, "")
        AWS_SESSION_TOKEN     = try(local.aws_env.aws_session_token, "")
      }
    )
  }
}

resource "null_resource" "alb_apply_transform_prom" {
  depends_on = [aws_lb_listener_rule.r_prom, local_file.alb_transform_prom]
  triggers = {
    rule_arn = aws_lb_listener_rule.r_prom.arn
    # Hash the intended content instead of the file, since the file doesn't exist yet at plan time
    transform = sha1(local_file.alb_transform_prom.content)
  }

  provisioner "local-exec" {
    command = "aws elbv2 modify-rule --region ${var.region} --rule-arn ${aws_lb_listener_rule.r_prom.arn} --transforms file://${replace(path.module, "\\", "/")}/alb_transform_prom.json"
    environment = merge(
      {
        AWS_REGION         = var.region
        AWS_DEFAULT_REGION = var.region
      },
      var.aws_profile != "" ? { AWS_PROFILE = var.aws_profile } : {},
      {
        AWS_ACCESS_KEY_ID     = try(local.aws_env.aws_access_key_id, "")
        AWS_SECRET_ACCESS_KEY = try(local.aws_env.aws_secret_access_key, "")
        AWS_SESSION_TOKEN     = try(local.aws_env.aws_session_token, "")
      }
    )
  }
}

# ========== Outputs ==========
output "public_ips" {
  value = {
    core   = "ASG-managed"
    auth   = aws_instance.auth.public_ip
    worker = aws_instance.worker.public_ip
    obs    = aws_instance.obs.public_ip
  }
}

output "private_ips" {
  value = {
    core   = "ASG-managed"
    auth   = aws_instance.auth.private_ip
    worker = aws_instance.worker.private_ip
    obs    = aws_instance.obs.private_ip
  }
}

output "alb_dns_name" {
  value       = aws_lb.public.dns_name
  description = "DNS del ALB público"
}

# URLs públicas de servicios detrás del ALB
output "service_urls" {
  description = "Public URLs via ALB"
  value = {
    base               = "http://${aws_lb.public.dns_name}"
    api_health         = "http://${aws_lb.public.dns_name}/api/health"
    api_docs           = "http://${aws_lb.public.dns_name}/api/docs"
    api_openapi        = "http://${aws_lb.public.dns_name}/api/openapi.json"
    auth_status        = "http://${aws_lb.public.dns_name}/auth/api/v1/status"
    auth_docs          = "http://${aws_lb.public.dns_name}/auth/docs"
    auth_openapi       = "http://${aws_lb.public.dns_name}/auth/openapi.json"
    grafana            = "http://${aws_lb.public.dns_name}/grafana/"
    prometheus         = "http://${aws_lb.public.dns_name}/prometheus/"
    prometheus_targets = "http://${aws_lb.public.dns_name}/prometheus/targets"
    loki_push          = "http://${aws_lb.public.dns_name}/loki/api/v1/push"
    health             = "http://${aws_lb.public.dns_name}/nginx-health"
  }
}

## Descubrimiento de instancias CORE lanzadas por el ASG (para referencia)
data "aws_instances" "core" {
  filter {
    name   = "tag:Name"
    values = ["anb-core"]
  }
  filter {
    name   = "instance-state-name"
    values = ["pending", "running"]
  }
}

output "core_asg_instance_ids" {
  description = "Instance IDs in the CORE ASG"
  value       = data.aws_instances.core.ids
}

output "core_asg_public_ips" {
  description = "Public IPs of CORE ASG instances"
  value       = data.aws_instances.core.public_ips
}

output "core_asg_private_ips" {
  description = "Private IPs of CORE ASG instances"
  value       = data.aws_instances.core.private_ips
}

output "rds_endpoints" {
  description = "RDS endpoints (host:port)"
  value = {
    core = aws_db_instance.core.endpoint
    auth = aws_db_instance.auth.endpoint
  }
}

output "rds_addresses" {
  description = "RDS addresses (hostname only, sin puerto)"
  value = {
    core = aws_db_instance.core.address
    auth = aws_db_instance.auth.address
  }
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3"
  value       = aws_s3_bucket.anb_videos.bucket
}

output "sqs_queue_url" {
  description = "URL de la cola SQS principal"
  value       = aws_sqs_queue.video_tasks.url
}

output "sqs_queue_arn" {
  description = "ARN de la cola SQS principal"
  value       = aws_sqs_queue.video_tasks.arn
}

output "sqs_dlq_url" {
  description = "URL de la DLQ de SQS"
  value       = aws_sqs_queue.video_dlq.url
}

output "sqs_dlq_arn" {
  description = "ARN de la DLQ de SQS"
  value       = aws_sqs_queue.video_dlq.arn
}
