variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_id" { type = string }
variable "instance_class" { type = string }
variable "publicly_accessible" {
  type    = bool
  default = false
}

locals {
  name = "${var.project_name}-${var.environment}"
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-db"
  subnet_ids = var.subnet_ids
  tags       = { Name = "${local.name}-db-subnets" }
}

resource "aws_secretsmanager_secret" "db" {
  name                    = "${local.name}/rds/credentials"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = "kahani"
    password = random_password.db.result
    dbname   = "kahani"
  })
}

resource "aws_db_instance" "this" {
  identifier                 = "${local.name}-pg"
  engine                     = "postgres"
  engine_version             = "16"
  instance_class             = var.instance_class
  allocated_storage          = 20
  max_allocated_storage      = 100
  storage_type               = "gp3"
  db_name                    = "kahani"
  username                   = "kahani"
  password                   = random_password.db.result
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = [var.security_group_id]
  publicly_accessible        = var.publicly_accessible
  multi_az                   = false
  # Free-tier accounts reject retention > 1; use 0 locally / hackathon.
  backup_retention_period    = 0
  skip_final_snapshot        = true
  deletion_protection        = false
  auto_minor_version_upgrade = true
  tags                       = { Name = "${local.name}-pg" }

  lifecycle {
    ignore_changes = [password]
  }
}

output "endpoint" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

output "database_url" {
  sensitive = true
  value     = "postgresql+asyncpg://kahani:${random_password.db.result}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/kahani?ssl=require"
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}
