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

# Si el lab tiene un Key Pair llamado 'vockey', úsalo.
# Si no, deja "" y NO se adjunta llave (sin SSH).
variable "key_name" {
  type        = string
  description = "Nombre de Key Pair existente (p.ej. 'vockey' en AWS Academy). Vacío = sin SSH."
  default     = "vockey"
}

variable "admin_cidr" {
  type        = string
  description = "CIDR permitido para SSH/UIs (ej: 186.80.29.7/32)."
  default     = "0.0.0.0/0"
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0))
    error_message = "admin_cidr debe ser un CIDR válido, ej: 1.2.3.4/32."
  }
}

# Fija AMI manual si quieres (si no, usa Ubuntu 22.04 más abajo)
variable "ami_id" {
  type    = string
  default = ""
}

# Preferimos 1a para evitar la 1e (que a veces no soporta algunos tipos)
variable "az_name" {
  type        = string
  description = "AZ preferida (ej: us-east-1a). Si no existe, se usa la primera subred del VPC."
  default     = "us-east-1a"
}

# Tipos por rol (compatibles con lab)
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

# Todas las subnets del VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Subnets en la AZ preferida
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
  # Si hay subred en la AZ elegida, úsala; si no, usa la primera del VPC
  subnet_id = length(data.aws_subnets.az.ids) > 0 ? element(data.aws_subnets.az.ids, 0) : element(data.aws_subnets.default.ids, 0)
  ami_id    = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu22.id
  tags_base = { Project = "ANB", Environment = "lab" }
}

# ========== Security Groups ==========
# Nota: sin 'egress {}' y con ignore_changes=[egress] para evitar Revoke prohibido en el lab

# WEB: 80 público
resource "aws_security_group" "web" {
  name        = "anb-web-sg"
  description = "WEB ingress 80"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
}

resource "aws_security_group_rule" "web_http" {
  type              = "ingress"
  security_group_id = aws_security_group.web.id
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
}

# CORE: 8000 (API), 8001 (Auth) solo desde WEB
resource "aws_security_group" "core" {
  name        = "anb-core-sg"
  description = "CORE ingress from WEB"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
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

# DB: 5432 (core), 5433 (auth) desde CORE y WORKER
resource "aws_security_group" "db" {
  name        = "anb-db-sg"
  description = "DB ingress from CORE & WORKER"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
}

resource "aws_security_group" "worker" {
  name        = "anb-worker-sg"
  description = "WORKER"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
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

# MQ: 5672 desde CORE y WORKER; 15672 UI solo admin
resource "aws_security_group" "mq" {
  name        = "anb-mq-sg"
  description = "RabbitMQ ingress"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
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

# OBS: 9090, 3000, 3100 solo admin
resource "aws_security_group" "obs" {
  name        = "anb-obs-sg"
  description = "Observability UIs"
  vpc_id      = data.aws_vpc.default.id

  lifecycle { ignore_changes = [egress] }

  tags = local.tags_base
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

# ========== User-data: instala Docker + Compose ==========
locals {
  user_data_ubuntu = <<-EOF
    #!/bin/bash
    set -eux
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings || true
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    usermod -aG docker ubuntu || true
    mkdir -p /opt/anb-cloud
  EOF
}

# ========== EC2 por rol ==========
resource "aws_instance" "web" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_web
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.web.id]
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-web" })
  root_block_device {
    volume_size = 20
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
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-core" })
  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }
}

resource "aws_instance" "db" {
  ami                         = local.ami_id
  instance_type               = var.instance_type_db
  subnet_id                   = local.subnet_id
  associate_public_ip_address = true
  key_name                    = var.key_name == "" ? null : var.key_name
  vpc_security_group_ids      = [aws_security_group.db.id]
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-db" })
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
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-mq" })
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
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-worker" })
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
  user_data                   = local.user_data_ubuntu
  tags                        = merge(local.tags_base, { Name = "anb-obs" })
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
