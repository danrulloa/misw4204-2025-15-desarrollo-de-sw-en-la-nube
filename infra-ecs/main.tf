terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  token      = var.aws_session_token
}

# ==========================================
# 1. DATA SOURCES & IAM (El "Truco" del LabRole)
# ==========================================
data "aws_availability_zones" "available" {}
data "aws_caller_identity" "current" {}

# IMPORTANTE: Usamos el rol pre-existente de AWS Academy
# Esto evita el error "User is not authorized to perform: iam:CreateRole"
data "aws_iam_role" "lab_role" {
  name = "LabRole" 
}

# ==========================================
# 2. NETWORKING (VPC & Subnets)
# ==========================================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "anb-ecs-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "anb-ecs-igw" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "anb-public-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "anb-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ==========================================
# 3. SECURITY GROUPS
# ==========================================
resource "aws_security_group" "alb_sg" {
  name        = "anb-alb-sg"
  description = "Allow HTTP traffic to ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks_sg" {
  name        = "anb-ecs-tasks-sg"
  description = "Allow traffic from ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "anb-rds-sg"
  description = "Allow traffic from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks_sg.id]
  }
}

# ==========================================
# 4. RECURSOS COMPARTIDOS (RDS, SQS, S3)
# ==========================================
# S3 Bucket para videos
resource "aws_s3_bucket" "videos" {
  bucket        = "anb-videos-${random_id.bucket_suffix.hex}"
  force_destroy = true
}
resource "random_id" "bucket_suffix" { byte_length = 4 }

# SQS Queue para Celery
resource "aws_sqs_queue" "celery_queue" {
  name = "anb-celery-queue"
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier             = "anb-db"
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "anb_db"
  username               = var.db_username
  password               = var.db_password
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  skip_final_snapshot    = true
  publicly_accessible    = false
}

resource "aws_db_subnet_group" "main" {
  name       = "anb-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id
}

# ==========================================
# 5. ECS CLUSTER & LOGS
# ==========================================
resource "aws_ecs_cluster" "main" {
  name = "anb-cluster"
}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/anb-apps"
  retention_in_days = 7
}

# ==========================================
# 6. LOAD BALANCER (ALB)
# ==========================================
resource "aws_lb" "main" {
  name               = "anb-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "404: Not Found"
      status_code  = "404"
    }
  }
}

# Target Groups
resource "aws_lb_target_group" "core" {
  name        = "anb-core-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # Requerido para Fargate

  health_check {
    path                = "/health"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "auth" {
  name        = "anb-auth-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200-399"
  }
}

# Reglas del Listener
resource "aws_lb_listener_rule" "core" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.core.arn
  }
  condition {
    path_pattern { values = ["/api/*"] }
  }
}

resource "aws_lb_listener_rule" "auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.auth.arn
  }
  condition {
    path_pattern { values = ["/auth/*"] }
  }
}

# ==========================================
# 7. TASK DEFINITIONS
# ==========================================
# --- CORE API ---
resource "aws_ecs_task_definition" "core" {
  family                   = "anb-core"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = data.aws_iam_role.lab_role.arn
  task_role_arn            = data.aws_iam_role.lab_role.arn

  container_definitions = jsonencode([
    {
      name      = "anb_api"
      image     = "ftaboadar/anb-core:latest"
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = [
        { name = "DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/anb_db" },
        { name = "CELERY_BROKER_URL", value = "sqs://" },
        { name = "SQS_QUEUE_NAME", value = "video_tasks" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_ACCESS_KEY_ID", value = var.aws_access_key },
        { name = "AWS_SECRET_ACCESS_KEY", value = var.aws_secret_key },
        { name = "AWS_SESSION_TOKEN", value = var.aws_session_token },
        { name = "JWT_SECRET", value = var.jwt_secret },
        { name = "ALGORITHM", value = "HS256" },
        { name = "ACCESS_TOKEN_SECRET_KEY", value = var.jwt_secret },
        { name = "S3_BUCKET", value = aws_s3_bucket.videos.bucket },
        { name = "S3_REGION", value = var.aws_region }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "core"
        }
      }
    }
  ])
}

# --- WORKER ---
resource "aws_ecs_task_definition" "worker" {
  family                   = "anb-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024 # Más CPU para FFmpeg
  memory                   = 2048 # Más RAM para video
  execution_role_arn       = data.aws_iam_role.lab_role.arn
  task_role_arn            = data.aws_iam_role.lab_role.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "ftaboadar/anb-worker:latest" # Asumiendo que tienes esta imagen
      essential = true
      environment = [
        { name = "DB_URL_CORE", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/anb_db" },
        { name = "CELERY_BROKER_URL", value = "sqs://" },
        { name = "SQS_QUEUE_NAME", value = "video_tasks" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_ACCESS_KEY_ID", value = var.aws_access_key },
        { name = "AWS_SECRET_ACCESS_KEY", value = var.aws_secret_key },
        { name = "AWS_SESSION_TOKEN", value = var.aws_session_token },
        { name = "S3_BUCKET", value = aws_s3_bucket.videos.bucket },
        { name = "S3_REGION", value = var.aws_region },
        { name = "ANB_INOUT_PATH", value = "/app/assets/inout.mp4" },
        { name = "ANB_WATERMARK_PATH", value = "/app/assets/watermark.png" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

# --- AUTH ---
resource "aws_ecs_task_definition" "auth" {
  family                   = "anb-auth"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = data.aws_iam_role.lab_role.arn
  task_role_arn            = data.aws_iam_role.lab_role.arn

  container_definitions = jsonencode([
    {
      name      = "anb_auth"
      image     = "ftaboadar/anb-auth:latest" # Asumiendo imagen
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = [
        { name = "DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/anb_db" },
        { name = "JWT_SECRET", value = var.jwt_secret },
        { name = "ALGORITHM", value = "HS256" },
        { name = "ACCESS_TOKEN_SECRET_KEY", value = var.jwt_secret },
        { name = "REFRESH_TOKEN_SECRET_KEY", value = var.jwt_secret },
        { name = "TOKEN_EXPIRE", value = "600" }
      ],
    logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "auth"
        }
      }
    }
  ])
}

# ==========================================
# 8. ECS SERVICES
# ==========================================
resource "aws_ecs_service" "core" {
  name            = "anb-core-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.core.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.core.arn
    container_name   = "anb_api"
    container_port   = 8000
  }
}

resource "aws_ecs_service" "auth" {
  name            = "anb-auth-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.auth.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.auth.arn
    container_name   = "anb_auth"
    container_port   = 8000
  }
}

resource "aws_ecs_service" "worker" {
  name            = "anb-worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks_sg.id]
    assign_public_ip = true
  }
  # Worker NO necesita Load Balancer
}

# ==========================================
# 9. AUTO SCALING
# ==========================================
# --- CORE (CPU Based) ---
resource "aws_appautoscaling_target" "core_target" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.core.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "core_cpu" {
  name               = "core-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.core_target.resource_id
  scalable_dimension = aws_appautoscaling_target.core_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.core_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 60.0
  }
}

# --- WORKER (CPU Based) ---
resource "aws_appautoscaling_target" "worker_target" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "worker_cpu" {
  name               = "worker-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker_target.resource_id
  scalable_dimension = aws_appautoscaling_target.worker_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 60.0
  }
}
