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
  default     = "t3.micro"
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

variable "ebs_data_volume_size" {
  description = "Extra EBS data volume size in GiB (keep small for student project)."
  type        = number
  default     = 8
}

variable "enable_implementation2" {
  description = "Enable serverless + container implementation resources."
  type        = bool
  default     = true
}

variable "enable_aurora_serverless" {
  description = "Enable Aurora Serverless v2 (optional due potential non-free-tier cost)."
  type        = bool
  default     = false
}

variable "serverless_frontend_index_file" {
  description = "Relative path to basic static index file for serverless frontend bucket."
  type        = string
  default     = "static/index.html"
}

# Enable/disable the ALB + Auto Scaling stack for scalability demonstration.
variable "enable_scalability_stack" {
  description = "Enable ALB + Auto Scaling resources for CA scalability evaluation."
  type        = bool
  default     = true
}

# Keep this small and free-tier conscious.
variable "asg_instance_type" {
  description = "EC2 instance type used by Auto Scaling instances."
  type        = string
  default     = "t3.micro"
}

variable "asg_min_size" {
  description = "Minimum number of instances in Auto Scaling Group."
  type        = number
  default     = 1
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in Auto Scaling Group."
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of instances in Auto Scaling Group."
  type        = number
  default     = 2
}
