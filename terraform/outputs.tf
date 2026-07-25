output "aws_region" {
  value = var.aws_region
}

output "alb_dns_name" {
  description = "Cloudflare CNAME target for api.uselamp.app (DNS-only / grey cloud)"
  value       = module.alb.alb_dns_name
}

output "api_domain" {
  value = var.api_domain
}

output "acm_validation_records" {
  description = "Add these DNS records in Cloudflare to validate the ACM certificate"
  value       = module.alb.acm_validation_records
}

output "acm_certificate_arn" {
  value = module.alb.acm_certificate_arn
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "ecr_repository_name" {
  value = module.ecr.repository_name
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecs_service_api" {
  value = module.ecs.api_service_name
}

output "ecs_service_worker" {
  value = module.ecs.worker_service_name
}

output "rds_endpoint" {
  value = module.rds.endpoint
}

output "redis_endpoint" {
  value = module.redis.endpoint
}

output "redis_url" {
  value     = module.redis.redis_url
  sensitive = true
}

output "allowed_origins" {
  value = local.allowed_origins
}

output "artifacts_bucket" {
  value = module.s3.bucket_name
}

output "app_secret_arn" {
  description = "Secrets Manager JSON for all api/worker runtime env (synced from .env)"
  value       = module.ecs.app_secret_arn
}

output "api_task_definition_arn" {
  value = module.ecs.api_task_definition_arn
}

output "worker_task_definition_arn" {
  value = module.ecs.worker_task_definition_arn
}

output "github_actions_role_arn" {
  description = "Set as GitHub Actions secret AWS_ROLE_ARN (OIDC)"
  value       = module.github_oidc.role_arn
}

output "vite_api_base_url" {
  description = "Set as Vercel / GitHub var VITE_API_BASE_URL after HTTPS is live"
  value       = "https://${var.api_domain}"
}
