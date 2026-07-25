variable "aws_region" {
  type        = string
  description = "AWS region for all resources (e.g. ap-south-2 for Hyderabad)"
  default     = "ap-south-2"
}

variable "project_name" {
  type        = string
  description = "Short name used in resource names"
  default     = "kahani"
}

variable "environment" {
  type        = string
  description = "Environment label (dev, staging, prod)"
  default     = "dev"
}

variable "api_domain" {
  type        = string
  description = "Public API hostname (Cloudflare CNAME → ALB)"
  default     = "api.uselamp.app"
}

variable "web_origins" {
  type        = list(string)
  description = "CORS allowed origins for the API"
  default = [
    "https://uselamp.app",
    "https://www.uselamp.app",
    "https://kahani-studio-three.vercel.app",
  ]
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "worker_cpu" {
  type    = number
  default = 512
}

variable "worker_memory" {
  type    = number
  default = 1024
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "github_org" {
  type        = string
  description = "GitHub org or user for OIDC trust (e.g. my-org)"
  default     = ""
}

variable "github_repo" {
  type        = string
  description = "GitHub repo name for OIDC trust (e.g. Kissa)"
  default     = "Kissa"
}

variable "image_tag" {
  type        = string
  description = "Initial container image tag (CI overwrites on deploy)"
  default     = "latest"
}

variable "enable_https" {
  type        = bool
  description = "Enable ALB HTTPS listener after ACM DNS validation in Cloudflare"
  default     = false
}
