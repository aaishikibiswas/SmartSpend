variable "aws_region" {
  description = "AWS region for SmartSpend infrastructure."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "smartspend"
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Existing EC2 key pair name for SSH access."
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH into the instance."
  type        = string
  default     = "0.0.0.0/0"
}
