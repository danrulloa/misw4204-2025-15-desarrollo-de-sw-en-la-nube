output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for videos"
  value       = aws_s3_bucket.videos.id
}

output "sqs_queue_url" {
  description = "URL of the SQS queue for Celery"
  value       = aws_sqs_queue.celery_queue.url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group for ECS tasks"
  value       = aws_cloudwatch_log_group.ecs_logs.name
}
