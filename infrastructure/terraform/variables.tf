variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for all resources"
  type        = string
  default     = "risk-intel"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "risk_app"
}

variable "db_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "risk_intel"
}

variable "raw_data_retention_days" {
  description = "Days to retain objects in the S3 data lake before expiry (cost control)"
  type        = number
  default     = 30
}
