locals {
  name            = "${var.project_name}-${var.environment}"
  allowed_origins = jsonencode(var.web_origins)
}

module "network" {
  source       = "./modules/network"
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

module "rds" {
  source              = "./modules/rds"
  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.network.vpc_id
  subnet_ids          = module.network.private_subnet_ids
  security_group_id   = module.network.rds_security_group_id
  instance_class      = var.db_instance_class
  publicly_accessible = false
}

module "redis" {
  source             = "./modules/redis"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  security_group_id  = module.network.redis_security_group_id
  node_type          = var.redis_node_type
}

module "s3" {
  source       = "./modules/s3"
  project_name = var.project_name
  environment  = var.environment
}

module "ecr" {
  source       = "./modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

module "alb" {
  source            = "./modules/alb"
  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  security_group_id = module.network.alb_security_group_id
  api_domain        = var.api_domain
  enable_https      = var.enable_https
}

module "ecs" {
  source                = "./modules/ecs"
  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  private_subnet_ids    = module.network.private_subnet_ids
  ecs_security_group_id = module.network.ecs_security_group_id
  target_group_arn      = module.alb.target_group_arn
  ecr_repository_url    = module.ecr.repository_url
  image_tag             = var.image_tag
  artifacts_bucket      = module.s3.bucket_name
  artifacts_bucket_arn  = module.s3.bucket_arn
  database_url          = module.rds.database_url
  redis_url             = module.redis.redis_url
  allowed_origins       = local.allowed_origins
  api_cpu               = var.api_cpu
  api_memory            = var.api_memory
  worker_cpu            = var.worker_cpu
  worker_memory         = var.worker_memory
  api_desired_count     = var.api_desired_count
  worker_desired_count  = var.worker_desired_count
}

module "github_oidc" {
  source             = "./modules/github_oidc"
  project_name       = var.project_name
  environment        = var.environment
  github_org         = var.github_org
  github_repo        = var.github_repo
  ecr_repository_arn = module.ecr.repository_arn
}
