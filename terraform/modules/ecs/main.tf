variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "ecs_security_group_id" { type = string }
variable "target_group_arn" { type = string }
variable "ecr_repository_url" { type = string }
variable "image_tag" { type = string }
variable "artifacts_bucket" { type = string }
variable "artifacts_bucket_arn" { type = string }
variable "database_url" {
  type      = string
  sensitive = true
}
variable "redis_url" { type = string }
variable "allowed_origins" { type = string }
variable "api_cpu" { type = number }
variable "api_memory" { type = number }
variable "worker_cpu" { type = number }
variable "worker_memory" { type = number }
variable "api_desired_count" { type = number }
variable "worker_desired_count" { type = number }

locals {
  name  = "${var.project_name}-${var.environment}"
  image = "${var.ecr_repository_url}:${var.image_tag}"

  # All app runtime config comes from Secrets Manager (synced from root .env).
  # Infra-managed keys are seeded here and protected by sync-app-secrets.sh.
  app_secret_keys = [
    "DATABASE_URL",
    "REDIS_URL",
    "DATA_DIR",
    "ARTIFACTS_BUCKET",
    "ALLOWED_ORIGINS",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LLM_MODEL",
    "TTS_PROVIDER",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_DEFAULT_MODEL_ID",
    "ELEVENLABS_DEFAULT_OUTPUT_FORMAT",
    "DATABRICKS_HOST",
    "DATABRICKS_TOKEN",
    "DATABRICKS_VECTOR_SEARCH_ENDPOINT",
    "DATABRICKS_VECTOR_SEARCH_INDEX",
    "DATABRICKS_VECTOR_SEARCH_COLUMNS",
    "DATABRICKS_CATALOG",
    "DATABRICKS_SCHEMA",
    "DATABRICKS_CAST_TABLE",
    "DATABRICKS_EMBEDDING_ENDPOINT",
  ]

  app_secrets = [
    for key in local.app_secret_keys : {
      name      = key
      valueFrom = "${aws_secretsmanager_secret.app.arn}:${key}::"
    }
  ]

  # Seed only — real values managed by sync-app-secrets.sh / Console.
  app_secret_seed = {
    DATABASE_URL                       = var.database_url
    REDIS_URL                          = var.redis_url
    DATA_DIR                           = "/data"
    ARTIFACTS_BUCKET                   = var.artifacts_bucket
    ALLOWED_ORIGINS                    = var.allowed_origins
    LLM_PROVIDER                       = "openai"
    LLM_API_KEY                        = ""
    LLM_MODEL                          = "gpt-4o"
    TTS_PROVIDER                       = "elevenlabs"
    ELEVENLABS_API_KEY                 = ""
    ELEVENLABS_DEFAULT_MODEL_ID        = "eleven_v3"
    ELEVENLABS_DEFAULT_OUTPUT_FORMAT   = "mp3_44100_128"
    DATABRICKS_HOST                    = ""
    DATABRICKS_TOKEN                   = ""
    DATABRICKS_VECTOR_SEARCH_ENDPOINT  = "kissa-vector-search"
    DATABRICKS_VECTOR_SEARCH_INDEX     = "workspace.kissa.cast_assets_index"
    DATABRICKS_VECTOR_SEARCH_COLUMNS   = "id,asset_type,provider_id,name,language,gender,description,preview_url,free_users_allowed"
    DATABRICKS_CATALOG                 = "workspace"
    DATABRICKS_SCHEMA                  = "kissa"
    DATABRICKS_CAST_TABLE              = "cast_assets"
    DATABRICKS_EMBEDDING_ENDPOINT      = "databricks-qwen3-embedding-0-6b"
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name}/api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.name}/worker"
  retention_in_days = 14
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.name}/app/secrets"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id     = aws_secretsmanager_secret.app.id
  secret_string = jsonencode(local.app_secret_seed)

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_iam_role" "execution" {
  name = "${local.name}-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "${local.name}-execution-secrets"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.app.arn]
    }]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "task_s3" {
  name = "${local.name}-task-s3"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [
        var.artifacts_bucket_arn,
        "${var.artifacts_bucket_arn}/*",
      ]
    }]
  })
}

resource "aws_ecs_cluster" "this" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
  tags = { Name = local.name }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = local.image
    essential = true
    command   = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    environment = []
    secrets     = local.app_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = local.image
    essential = true
    command   = ["arq", "worker.settings.WorkerSettings"]
    environment = []
    secrets     = local.app_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  depends_on = [aws_ecs_task_definition.api]
}

resource "aws_ecs_service" "worker" {
  name            = "${local.name}-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}

output "worker_service_name" {
  value = aws_ecs_service.worker.name
}

output "app_secret_arn" {
  value = aws_secretsmanager_secret.app.arn
}

output "api_task_definition_arn" {
  value = aws_ecs_task_definition.api.arn
}

output "worker_task_definition_arn" {
  value = aws_ecs_task_definition.worker.arn
}

output "api_task_definition_family" {
  value = aws_ecs_task_definition.api.family
}

output "worker_task_definition_family" {
  value = aws_ecs_task_definition.worker.family
}
