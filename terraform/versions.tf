terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Optional: uncomment and set bucket/key after creating a state bucket
  # backend "s3" {
  #   bucket = "kahani-terraform-state"
  #   key    = "dev/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}
