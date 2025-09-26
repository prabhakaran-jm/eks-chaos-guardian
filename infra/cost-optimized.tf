# EKS Chaos Guardian - Cost Optimized Infrastructure
# AWS AI Agent Hackathon 2025

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "eks-chaos-guardian"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {}

# Local values
locals {
  name = "eks-chaos-guardian"
  tags = {
    Project     = "EKS-Chaos-Guardian"
    Environment = "demo"
    Hackathon   = "AWS-AI-Agent-2025"
    CostCenter  = "hackathon-demo"
  }
}

# VPC Module - Cost optimized
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.name}-vpc"
  cidr = "10.0.0.0/16"

  # Use only 2 AZs to minimize costs
  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # Cost optimizations
  enable_nat_gateway = false  # Disable NAT Gateway to save costs
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true

  # Enable auto-assign public IP for public subnets (required for EKS nodes)
  map_public_ip_on_launch = true

  # Note: Without NAT Gateway, private subnets won't have internet access
  # This is acceptable for demo purposes to minimize costs

  tags = local.tags
}

# EKS Autopilot Cluster - Cost optimized
resource "aws_eks_cluster" "chaos_guardian" {
  name     = "${local.name}-autopilot"
  role_arn = aws_iam_role.cluster.arn
  version  = "1.29"

  vpc_config {
    subnet_ids              = concat(module.vpc.private_subnets, module.vpc.public_subnets)
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  # Enable EKS add-ons for cost optimization
  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_cloudwatch_log_group.cluster,
  ]

  tags = local.tags
}

# EKS Autopilot Node Group
resource "aws_eks_node_group" "autopilot" {
  cluster_name    = aws_eks_cluster.chaos_guardian.name
  node_group_name = "autopilot-nodes"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = module.vpc.public_subnets

  # Cost-optimized instance types
  instance_types = ["t3.small"]  # Smallest viable instance

  scaling_config {
    desired_size = 1  # Minimal nodes
    max_size     = 3  # Small scale
    min_size     = 1
  }

  update_config {
    max_unavailable_percentage = 50
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]

  tags = local.tags
}

# IAM Role for EKS Cluster
resource "aws_iam_role" "cluster" {
  name = "${local.name}-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

# IAM Role for EKS Node Group
resource "aws_iam_role" "node_group" {
  name = "${local.name}-node-group-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

# CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "cluster" {
  name              = "/aws/eks/${aws_eks_cluster.chaos_guardian.name}/cluster"
  retention_in_days = 3  # Cost optimization: short retention

  tags = local.tags
}

# S3 Bucket for runbook storage
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "chaos_guardian" {
  bucket = "${local.name}-${random_id.bucket_suffix.hex}"

  tags = local.tags
}

resource "aws_s3_bucket_versioning" "chaos_guardian" {
  bucket = aws_s3_bucket.chaos_guardian.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "chaos_guardian" {
  bucket = aws_s3_bucket.chaos_guardian.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Lifecycle Policy for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "chaos_guardian" {
  bucket = aws_s3_bucket.chaos_guardian.id

  rule {
    id     = "delete_old_logs"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 7  # Delete logs after 7 days
    }

    noncurrent_version_expiration {
      noncurrent_days = 3
    }
  }
}

# DynamoDB Table - On-demand for cost optimization
resource "aws_dynamodb_table" "runbook_index" {
  name           = "${local.name}-runbook-index"
  billing_mode   = "PAY_PER_REQUEST"  # Pay per request instead of provisioned
  hash_key       = "pattern_id"

  attribute {
    name = "pattern_id"
    type = "S"
  }

  tags = local.tags
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })

  tags = local.tags
}

# Lambda Policy
resource "aws_iam_policy" "lambda_policy" {
  name        = "${local.name}-lambda-policy"
  description = "Minimal policy for EKS Chaos Guardian Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.chaos_guardian.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.runbook_index.arn
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.lambda_execution_role.name
}

# Lambda Function
resource "aws_lambda_function" "bedrock_agent" {
  filename         = "../lambda/bedrock-agent/main.py.zip"
  function_name    = "${local.name}-bedrock-agent"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      S3_BUCKET_NAME      = aws_s3_bucket.chaos_guardian.id
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.runbook_index.name
      SLACK_WEBHOOK_URL   = var.slack_webhook_url
    }
  }

  tags = local.tags
}

# API Gateway
resource "aws_api_gateway_rest_api" "chaos_guardian_api" {
  name        = "${local.name}-api"
  description = "Minimal API Gateway for EKS Chaos Guardian"

  tags = local.tags
}

# Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.chaos_guardian.id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.chaos_guardian.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.chaos_guardian.certificate_authority[0].data
}

output "s3_bucket_name" {
  description = "S3 bucket name for runbook storage"
  value       = aws_s3_bucket.chaos_guardian.id
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = "https://${aws_api_gateway_rest_api.chaos_guardian_api.id}.execute-api.${var.aws_region}.amazonaws.com"
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    eks_cluster  = "$30 (Autopilot cluster)"
    node_group   = "$15 (t3.small instance)"
    lambda       = "$2 (minimal usage)"
    s3           = "$1 (minimal storage)"
    dynamodb     = "$1 (on-demand)"
    api_gateway  = "$1 (minimal usage)"
    nat_instance = "$5 (t3.nano)"
    total        = "~$55/month"
  }
}
