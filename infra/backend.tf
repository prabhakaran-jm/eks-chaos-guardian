# Terraform Backend Configuration
# S3 backend with DynamoDB state locking for team collaboration

terraform {
  backend "s3" {
    # S3 bucket for storing Terraform state
    bucket = "eks-chaos-guardian-terraform-state"
    
    # State file key
    key = "infrastructure/terraform.tfstate"
    
    # AWS region
    region = "us-east-1"
    
    # DynamoDB table for state locking
    dynamodb_table = "eks-chaos-guardian-terraform-locks"
    
    # Encrypt state file
    encrypt = true
    
    # Profile to use (matches our AWS SSO profile)
    profile = "eks-chaos-guardian"
  }
}
