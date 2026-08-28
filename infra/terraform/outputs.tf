output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster for the selected environment."
}

output "task_definition_arn" {
  value       = aws_ecs_task_definition.main.arn
  description = "Task definition with immutable API and web images."
}

output "api_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository URL for the API image."
}

output "web_repository_url" {
  value       = aws_ecr_repository.web.repository_url
  description = "ECR repository URL for the web image."
}
