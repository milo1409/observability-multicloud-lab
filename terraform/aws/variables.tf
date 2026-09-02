variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "obs-multicloud"
}

variable "environment" {
  type    = string
  default = "sandbox"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "db_name" {
  type    = string
  default = "observability"
}

variable "db_username" {
  type    = string
  default = "observability"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "enable_rds" {
  description = "Create RDS only when database evidence is needed"
  type        = bool
  default     = false
}

variable "enable_security_hub" {
  description = "Enable Security Hub only during security evidence collection"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  type    = number
  default = 1
}


variable "enable_ec2" {
  description = "Create one low-cost EC2 instance for the observability lab"
  type        = bool
  default     = false
}

variable "ec2_instance_type" {
  description = "Small instance for sandbox"
  type        = string
  default     = "t3.micro"
}

variable "service_a_allowed_cidr" {
  description = "CIDR allowed to reach service-a on port 8001"
  type        = string
  default     = "0.0.0.0/0"
}
