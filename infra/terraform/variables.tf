variable "aws_region" {
  type        = string
  description = "AWS region for the control plane artifacts."
  default     = "eu-central-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "api_image" {
  type        = string
  description = "Immutable Gatehouse API image URI."
  default     = "ghcr.io/kyan9400/gatehouse-api:0.1.0"
}

variable "web_image" {
  type        = string
  description = "Immutable Gatehouse web image URI."
  default     = "ghcr.io/kyan9400/gatehouse-web:0.1.0"
}

variable "execution_role_arn" {
  type        = string
  description = "Existing ECS task execution role ARN."
  default     = ""
}
