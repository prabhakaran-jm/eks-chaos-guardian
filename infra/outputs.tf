# EKS Chaos Guardian - Terraform Outputs

output "cluster_name" {
  description = "The name/id of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "cluster_primary_security_group_id" {
  description = "The cluster primary security group ID created by the EKS service"
  value       = module.eks.cluster_primary_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = module.eks.cluster_oidc_issuer_url
}

output "cluster_platform_version" {
  description = "Platform version for the EKS cluster"
  value       = module.eks.cluster_platform_version
}

output "cluster_status" {
  description = "Status of the EKS cluster"
  value       = module.eks.cluster_status
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

# Node Group Outputs
output "node_groups" {
  description = "EKS node groups"
  value = {
    for k, v in module.eks.eks_managed_node_groups : k => {
      arn  = v.node_group_arn
      name = v.node_group_name
      status = v.node_group_status
    }
  }
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC where the cluster and its nodes will be provisioned"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

# Storage Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for audit logs and runbooks"
  value       = aws_s3_bucket.chaos_guardian.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for audit logs and runbooks"
  value       = aws_s3_bucket.chaos_guardian.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for runbook index"
  value       = aws_dynamodb_table.runbook_index.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for runbook index"
  value       = aws_dynamodb_table.runbook_index.arn
}

# IAM Outputs
output "lambda_execution_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "lambda_execution_role_name" {
  description = "Name of the IAM role for Lambda execution"
  value       = aws_iam_role.lambda_execution_role.name
}

# API Gateway Outputs
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.chaos_guardian_api.id
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.chaos_guardian_api.id}.execute-api.${var.aws_region}.amazonaws.com"
}

# Connection Instructions
output "kubectl_config" {
  description = "Kubectl configuration command"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "setup_instructions" {
  description = "Setup instructions for the EKS Chaos Guardian"
  value = <<-EOT
    To get started with EKS Chaos Guardian:
    
    1. Configure kubectl:
       aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}
    
    2. Verify cluster access:
       kubectl get nodes
    
    3. Deploy demo applications:
       kubectl apply -f demo/apps/
    
    4. Run chaos scenarios:
       make demo-oom
       make demo-image-pull
       make demo-readiness-probe
       make demo-disk-pressure
       make demo-pdb-blocking
       make demo-coredns
    
    5. Monitor via CloudWatch:
       https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}
    
    API Gateway URL: https://${aws_api_gateway_rest_api.chaos_guardian_api.id}.execute-api.${var.aws_region}.amazonaws.com
    S3 Bucket: ${aws_s3_bucket.chaos_guardian.id}
    DynamoDB Table: ${aws_dynamodb_table.runbook_index.name}
  EOT
}
