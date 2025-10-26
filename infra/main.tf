terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
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

# Tipos por rol (compatibles con el lab)
variable "instance_type_web" {
  type    = string
  default = "t3.micro"
}
variable "instance_type_core" {
  type    = string
  default = "t3.micro"
}
variable "instance_type_db" {
  type    = string
  default = "t3.micro"
}
variable "instance_type_mq" {
  type    = string
  default = "t3.micro"
}
variable "instance_type_worker" {
  type    = string
  default = "t3.micro"
}
variable "instance_type_obs" {
  type    = string
  default = "t3.micro"
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

# WEB: 80 y 8080 públicos (8080 porque Nginx mapea 8080:80 en tu compose)
resource "aws_security_group" "web" {
  name        = "anb-web-sg"
  description = "WEB ingress 80/8080"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "web_http_80" {
  type              = "ingress"
  security_group_id = aws_security_group.web.id
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "web_http_8080" {
  type              = "ingress"
  security_group_id = aws_security_group.web.id
  from_port         = 8080
  to_port           = 8080
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# Reglas de egress para WEB (acceso a internet)
resource "aws_security_group_rule" "web_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.web.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "web_egress_udp" {
  type              = "egress"
  security_group_id = aws_security_group.web.id
  from_port         = 0
  to_port           = 65535
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# CORE: 8000 (API), 8001 (Auth) solo desde WEB
resource "aws_security_group" "core" {
  name        = "anb-core-sg"
  description = "CORE ingress from WEB"
  vpc_id      = data.aws_vpc.default.id
  tags        = local.tags_base
}

resource "aws_security_group_rule" "core_from_web_8000" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.web.id
}
resource "aws_security_group_rule" "core_from_web_8001" {
  type                     = "ingress"
  security_group_id        = aws_security_group.core.id
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.web.id
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

# Reglas de egress para WORKER (acceso a internet)
resource "aws_security_group_rule" "worker_egress_all" {
  type              = "egress"
  security_group_id = aws_security_group.worker.id
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
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
resource "aws_security_group_rule" "web_ssh" {
  type              = "ingress"
  security_group_id = aws_security_group.web.id
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_cidr]
}

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
    role   = "db", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip = "", core_ip = "", db_ip = "", mq_ip = "", worker_ip = "", obs_ip = ""
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
    role   = "mq", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip = "", core_ip = "", db_ip = "", mq_ip = "", worker_ip = "", obs_ip = ""
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
  depends_on                  = [aws_instance.db, aws_instance.mq]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role   = "core", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip = "", core_ip = "", db_ip = aws_instance.db.private_ip,
    mq_ip  = aws_instance.mq.private_ip, worker_ip = "", obs_ip = ""
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
  depends_on                  = [aws_instance.mq]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role   = "worker", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip = "", core_ip = "", db_ip = "", mq_ip = aws_instance.mq.private_ip, worker_ip = "", obs_ip = ""
  })
  tags = merge(local.tags_base, { Name = "anb-worker" })
  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }
}

resource "aws_instance" "web" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_web
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.web.id]
  depends_on                  = [aws_instance.core]
  user_data = templatefile("${path.module}/userdata.sh.tftpl", {
    role   = "web", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip = "", core_ip = aws_instance.core.private_ip, db_ip = "",
    mq_ip  = aws_instance.mq.private_ip, worker_ip = "", obs_ip = aws_instance.obs.private_ip
  })
  tags = merge(local.tags_base, { Name = "anb-web" })
  root_block_device {
    volume_size = 20
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
    role      = "obs", repo_url = var.repo_url, repo_branch = var.repo_branch, compose_file = var.compose_file,
    web_ip    = "",
    core_ip   = aws_instance.core.private_ip,
    db_ip     = aws_instance.db.private_ip,
    mq_ip     = aws_instance.mq.private_ip,
    worker_ip = aws_instance.worker.private_ip,
    obs_ip    = ""
  })
  tags = merge(local.tags_base, { Name = "anb-obs" })
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
}

# ========== Outputs ==========
output "public_ips" {
  value = {
    web    = aws_instance.web.public_ip
    core   = aws_instance.core.public_ip
    db     = aws_instance.db.public_ip
    mq     = aws_instance.mq.public_ip
    worker = aws_instance.worker.public_ip
    obs    = aws_instance.obs.public_ip
  }
}

output "private_ips" {
  value = {
    web    = aws_instance.web.private_ip
    core   = aws_instance.core.private_ip
    db     = aws_instance.db.private_ip
    mq     = aws_instance.mq.private_ip
    worker = aws_instance.worker.private_ip
    obs    = aws_instance.obs.private_ip
  }
}
