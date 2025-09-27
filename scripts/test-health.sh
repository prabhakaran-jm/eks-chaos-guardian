#!/bin/bash

# EKS Chaos Guardian - Health Check Script
# Quick test to verify all components are working

echo "🔍 EKS Chaos Guardian Health Check"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

echo -e "\n${YELLOW}1. Checking AWS CLI Configuration...${NC}"
aws sts get-caller-identity --profile eks-chaos-guardian > /dev/null 2>&1
check_status "AWS CLI configured"

echo -e "\n${YELLOW}2. Checking EKS Cluster...${NC}"
aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian > /dev/null 2>&1
check_status "EKS cluster accessible"

echo -e "\n${YELLOW}3. Checking Lambda Functions...${NC}"
aws lambda list-functions --profile eks-chaos-guardian | grep -q "eks-chaos-guardian" > /dev/null 2>&1
check_status "Lambda functions deployed"

echo -e "\n${YELLOW}4. Checking S3 Bucket...${NC}"
aws s3 ls s3://eks-chaos-guardian-runbooks --profile eks-chaos-guardian > /dev/null 2>&1
check_status "S3 bucket accessible"

echo -e "\n${YELLOW}5. Checking DynamoDB Table...${NC}"
aws dynamodb describe-table --table-name eks-chaos-guardian-runbook-index --profile eks-chaos-guardian > /dev/null 2>&1
check_status "DynamoDB table exists"

echo -e "\n${YELLOW}6. Testing Lambda Function (Dry Run)...${NC}"
aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' /tmp/response.json --profile eks-chaos-guardian > /dev/null 2>&1
check_status "Lambda function test"

echo -e "\n${YELLOW}7. Checking Kubernetes Access...${NC}"
kubectl get nodes > /dev/null 2>&1
check_status "Kubernetes cluster accessible"

echo -e "\n${YELLOW}8. Checking Web UI...${NC}"
curl -s http://localhost:5000 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Web UI running${NC}"
else
    echo -e "${YELLOW}⚠️  Web UI not running (start with: cd ui && python server.py)${NC}"
fi

echo -e "\n${YELLOW}9. Checking Demo Scenarios...${NC}"
if [ -f "demo/scenarios/oomkilled.py" ]; then
    echo -e "${GREEN}✅ Demo scenarios available${NC}"
else
    echo -e "${RED}❌ Demo scenarios missing${NC}"
fi

echo -e "\n${YELLOW}10. Checking Documentation...${NC}"
if [ -f "README.md" ] && [ -f "docs/architecture.md" ]; then
    echo -e "${GREEN}✅ Documentation complete${NC}"
else
    echo -e "${RED}❌ Documentation missing${NC}"
fi

echo -e "\n${YELLOW}=================================="
echo -e "Health Check Complete!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Run: ./test-all.sh (comprehensive tests)"
echo "2. Run: ./demo-scenario.sh oomkilled (demo scenario)"
echo "3. Start Web UI: cd ui && python server.py"
echo "4. Test Slack bot with configured webhook"
