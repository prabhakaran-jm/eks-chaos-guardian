# PowerShell script to set up Terraform backend resources
# Run this before initializing Terraform with the S3 backend

Write-Host "🚀 Setting up Terraform backend resources..." -ForegroundColor Green

# Set AWS profile
$env:AWS_PROFILE = "eks-chaos-guardian"

# S3 bucket name for Terraform state
$bucketName = "eks-chaos-guardian-terraform-state"
$region = "us-east-1"

Write-Host "📦 Creating S3 bucket for Terraform state: $bucketName" -ForegroundColor Yellow

# Create S3 bucket
aws s3 mb s3://$bucketName --region $region

# Enable versioning on the bucket
aws s3api put-bucket-versioning --bucket $bucketName --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption --bucket $bucketName --server-side-encryption-configuration '{
    "Rules": [
        {
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }
    ]
}'

# Block public access
aws s3api put-public-access-block --bucket $bucketName --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
}'

Write-Host "🔒 Creating DynamoDB table for state locking..." -ForegroundColor Yellow

# Create DynamoDB table for state locking
aws dynamodb create-table `
    --table-name eks-chaos-guardian-terraform-locks `
    --attribute-definitions AttributeName=LockID,AttributeType=S `
    --key-schema AttributeName=LockID,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region $region

# Wait for table to be active
Write-Host "⏳ Waiting for DynamoDB table to be active..." -ForegroundColor Yellow
aws dynamodb wait table-exists --table-name eks-chaos-guardian-terraform-locks --region $region

Write-Host "✅ Backend setup complete!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Run: terraform init" -ForegroundColor White
Write-Host "   2. Run: terraform plan" -ForegroundColor White
Write-Host "   3. Run: terraform apply" -ForegroundColor White
