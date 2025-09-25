# EKS Chaos Guardian - Terraform Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

variable "node_instance_types" {
  description = "List of EC2 instance types for the EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes in the EKS node group"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes in the EKS node group"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes in the EKS node group"
  type        = number
  default     = 3
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "eks-chaos-guardian"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_bedrock_access" {
  description = "Enable Bedrock access for the Lambda functions"
  type        = bool
  default     = true
}

variable "chaos_test_namespace" {
  description = "Kubernetes namespace for chaos testing"
  type        = string
  default     = "chaos-test"
}

variable "demo_app_namespace" {
  description = "Kubernetes namespace for demo applications"
  type        = string
  default     = "demo-app"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "A map of tags to assign to the resources"
  type        = map(string)
  default = {
    Project     = "EKS-Chaos-Guardian"
    Environment = "demo"
    Hackathon   = "AWS-AI-Agent-2024"
  }
}
