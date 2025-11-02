terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    local  = { source = "hashicorp/local", version = "~> 2.5" }
    null   = { source = "hashicorp/null", version = "~> 3.2" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

# ========== Variables ==========
variable "region" {
  type    = string
  default = "us-east-1"
}
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

# Tipos por rol (compatibles con el lab)
variable "instance_type_web" {
  type    = string
  default = "t3.small"
}
variable "instance_type_core" {
  type    = string
  default = "t3.small"
}
variable "instance_type_db" {
  type    = string
  default = "t3.small"
}
variable "instance_type_mq" {
  type    = string
  default = "t3.small"
}
variable "instance_type_worker" {
  type    = string
  default = "t3.small"
}
variable "instance_type_obs" {
  type    = string
  default = "t3.small"
}

provider "aws" { region = var.region }

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
resource "aws_security_group_rule" "core_from_alb_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

# Allow Prometheus (OBS) to scrape CORE metrics (API 8000, Auth 8001) and cadvisor (8080)
resource "aws_security_group_rule" "core_from_obs_8000" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
resource "aws_security_group_rule" "core_from_obs_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
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

# DB: 5432 (core), 5433 (auth) desde CORE y 5432 desde WORKER
resource "aws_security_group" "db" {
  name        = "anb-db-sg"
  description = "DB ingress from CORE & WORKER"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group" "worker" {
  name        = "anb-worker-sg"
  description = "WORKER"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "db_from_core_5432" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
}
resource "aws_security_group_rule" "db_from_core_5433" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 5433
  to_port                  = 5433
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
}
resource "aws_security_group_rule" "db_from_worker_5432" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.worker.id
}

# Allow Prometheus (OBS) to scrape DB exporters and cadvisor
resource "aws_security_group_rule" "db_from_obs_9187" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 9187
  to_port                  = 9187
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
resource "aws_security_group_rule" "db_from_obs_9188" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 9188
  to_port                  = 9188
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
resource "aws_security_group_rule" "db_from_obs_8080" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

# Reglas de egress para DB (acceso a internet)
resource "aws_security_group_rule" "db_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.db.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "db_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.db.id
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

resource "aws_security_group_rule" "rds_ingress_from_worker" {
  type                     = "ingress"
  security_group_id        = aws_security_group.rds.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.worker.id
  description              = "Worker to RDS"
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

# MQ: 5672 desde CORE y WORKER; 15672 UI solo admin
resource "aws_security_group" "mq" {
  name        = "anb-mq-sg"
  description = "RabbitMQ ingress"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}
resource "aws_security_group_rule" "mq_from_core_5672" {
  type                     = "ingress"
  security_group_id        = aws_security_group.mq.id
  from_port                = 5672
  to_port                  = 5672
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.core.id
}
resource "aws_security_group_rule" "mq_from_worker_5672" {
  type                     = "ingress"
  security_group_id        = aws_security_group.mq.id
  from_port                = 5672
  to_port                  = 5672
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.worker.id
}
resource "aws_security_group_rule" "mq_ui_admin" {
  type              = "ingress"
  security_group_id = aws_security_group.mq.id
  from_port         = 15672
  to_port           = 15672
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

resource "aws_security_group_rule" "mq_from_alb_15672" {
  type                     = "ingress"
  security_group_id        = aws_security_group.mq.id
  from_port                = 15672
  to_port                  = 15672
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

# Allow Prometheus (OBS) to scrape RabbitMQ exporter and cadvisor
resource "aws_security_group_rule" "mq_from_obs_15692" {
  type                     = "ingress"
  security_group_id        = aws_security_group.mq.id
  from_port                = 15692
  to_port                  = 15692
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}
resource "aws_security_group_rule" "mq_from_obs_8080" {
  type                     = "ingress"
  security_group_id        = aws_security_group.mq.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.obs.id
}

# Reglas de egress para MQ (acceso a internet)
resource "aws_security_group_rule" "mq_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.mq.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "mq_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.mq.id
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

resource "aws_security_group_rule" "db_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

resource "aws_security_group_rule" "mq_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.mq.id
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
#   DB y MQ no dependen de nadie
#   CORE depende de DB/MQ
#   WORKER depende de MQ
#   WEB depende de CORE
#   OBS no depende de otros (Prometheus se puede configurar luego)

resource "aws_instance" "db" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_db
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.db.id]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "db",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    db_ip             = "",
    mq_ip             = "",
    worker_ip         = "",
    obs_ip            = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = "",
    rds_auth_endpoint = "",
    rds_password      = "",
    s3_bucket         = ""
  })
  tags = merge(local.tags_base, { Name = "anb-db" })
  root_block_device {
    volume_size = 80
    volume_type = "gp3"
  }
}

resource "aws_instance" "mq" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_mq
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.mq.id]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "mq",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    db_ip             = "",
    mq_ip             = "",
    worker_ip         = "",
    obs_ip            = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = "",
    rds_auth_endpoint = "",
    rds_password      = "",
    s3_bucket         = ""
  })
  tags = merge(local.tags_base, { Name = "anb-mq" })
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
}

resource "aws_instance" "core" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_core
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.core.id]
  depends_on                  = [aws_instance.db, aws_instance.mq, aws_db_instance.core, aws_db_instance.auth, aws_s3_bucket.anb_videos]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "core",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    db_ip             = "", # Ya no se usa (RDS en su lugar)
    mq_ip             = aws_instance.mq.private_ip,
    worker_ip         = "",
    obs_ip            = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = aws_db_instance.core.address,
    rds_auth_endpoint = aws_db_instance.auth.address,
    rds_password      = var.rds_password != "" ? var.rds_password : "anb_pass_change_me",
    s3_bucket         = aws_s3_bucket.anb_videos.bucket
  })
  tags = merge(local.tags_base, { Name = "anb-core" })
  root_block_device {
    volume_size = 40
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
  depends_on                  = [aws_instance.mq, aws_s3_bucket.anb_videos]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role              = "worker",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = "",
    db_ip             = "",
    mq_ip             = aws_instance.mq.private_ip,
    worker_ip         = "",
    obs_ip            = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = "", # Worker no necesita RDS directamente
    rds_auth_endpoint = "",
    rds_password      = "",
    s3_bucket         = aws_s3_bucket.anb_videos.bucket # Worker necesita S3 para leer videos
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
    role              = "obs",
    repo_url          = var.repo_url,
    repo_branch       = var.repo_branch,
    compose_file      = var.compose_file,
    web_ip            = "",
    core_ip           = aws_instance.core.private_ip,
    db_ip             = aws_instance.db.private_ip,
    mq_ip             = aws_instance.mq.private_ip,
    worker_ip         = aws_instance.worker.private_ip,
    obs_ip            = "",
    alb_dns           = aws_lb.public.dns_name,
    rds_core_endpoint = "",
    rds_auth_endpoint = "",
    rds_password      = "",
    s3_bucket         = ""
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
  tags   = local.tags_base
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

resource "aws_lb_target_group" "tg_rmq" {
  name        = "anb-tg-rmq"
  port        = 15672
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.aws_vpc.default.id
  health_check {
    path    = "/rabbitmq/"
    matcher = "200-399"
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

resource "aws_lb_listener_rule" "r_rmq_redirect" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30
  action {
    type = "redirect"
    redirect {
      host        = "#{host}"
      path        = "/rabbitmq/"
      protocol    = "#{protocol}"
      port        = "#{port}"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
  condition {
    path_pattern {
      values = ["/rabbitmq"]
    }
  }
}

resource "aws_lb_listener_rule" "r_rmq" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 31
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_rmq.arn
  }
  condition {
    path_pattern {
      values = ["/rabbitmq/*"]
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
resource "aws_lb_target_group_attachment" "att_api_core" {
  target_group_arn = aws_lb_target_group.tg_api.arn
  target_id        = aws_instance.core.id
}

resource "aws_lb_target_group_attachment" "att_auth_core" {
  target_group_arn = aws_lb_target_group.tg_auth.arn
  target_id        = aws_instance.core.id
}

resource "aws_lb_target_group_attachment" "att_rmq_mq" {
  target_group_arn = aws_lb_target_group.tg_rmq.arn
  target_id        = aws_instance.mq.id
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
    environment = {
      AWS_REGION         = var.region
      AWS_DEFAULT_REGION = var.region
    }
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
    environment = {
      AWS_REGION         = var.region
      AWS_DEFAULT_REGION = var.region
    }
  }
}

# ========== Outputs ==========
output "public_ips" {
  value = {
    core   = aws_instance.core.public_ip
    db     = aws_instance.db.public_ip
    mq     = aws_instance.mq.public_ip
    worker = aws_instance.worker.public_ip
    obs    = aws_instance.obs.public_ip
  }
}

output "private_ips" {
  value = {
    core   = aws_instance.core.private_ip
    db     = aws_instance.db.private_ip
    mq     = aws_instance.mq.private_ip
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
    rabbitmq_ui        = "http://${aws_lb.public.dns_name}/rabbitmq/"
    grafana            = "http://${aws_lb.public.dns_name}/grafana/"
    prometheus         = "http://${aws_lb.public.dns_name}/prometheus/"
    prometheus_targets = "http://${aws_lb.public.dns_name}/prometheus/targets"
    loki_push          = "http://${aws_lb.public.dns_name}/loki/api/v1/push"
    health             = "http://${aws_lb.public.dns_name}/nginx-health"
  }
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
