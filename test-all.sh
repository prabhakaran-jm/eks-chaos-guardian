#!/bin/bash

# EKS Chaos Guardian - Comprehensive Test Suite
# Tests all Lambda functions, integrations, and workflows

echo "🧪 EKS Chaos Guardian - Comprehensive Test Suite"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local command="$2"
    
    echo -e "\n${BLUE}Testing: $test_name${NC}"
    echo "Command: $command"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
    fi
}

# Function to test Lambda function with payload
test_lambda() {
    local function_name="$1"
    local payload="$2"
    local test_name="$3"
    
    echo -e "\n${BLUE}Testing Lambda: $function_name${NC}"
    echo "Payload: $payload"
    
    local response_file="/tmp/lambda_response_$(date +%s).json"
    
    if aws lambda invoke --function-name "$function_name" --payload "$payload" "$response_file" --profile eks-chaos-guardian > /dev/null 2>&1; then
        if [ -f "$response_file" ]; then
            local status_code=$(jq -r '.statusCode' "$response_file" 2>/dev/null)
            if [ "$status_code" = "200" ]; then
                echo -e "${GREEN}✅ PASSED: $test_name${NC}"
                ((TESTS_PASSED++))
            else
                echo -e "${RED}❌ FAILED: $test_name (Status: $status_code)${NC}"
                ((TESTS_FAILED++))
            fi
            rm -f "$response_file"
        else
            echo -e "${RED}❌ FAILED: $test_name (No response file)${NC}"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "${RED}❌ FAILED: $test_name (Lambda invoke failed)${NC}"
        ((TESTS_FAILED++))
    fi
}

echo -e "\n${YELLOW}Starting Comprehensive Test Suite...${NC}"

# 1. Infrastructure Tests
echo -e "\n${YELLOW}=== INFRASTRUCTURE TESTS ===${NC}"

run_test "AWS CLI Configuration" "aws sts get-caller-identity --profile eks-chaos-guardian"
run_test "EKS Cluster Access" "aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian"
run_test "Kubernetes Access" "kubectl get nodes"
run_test "S3 Bucket Access" "aws s3 ls s3://eks-chaos-guardian-runbooks --profile eks-chaos-guardian"
run_test "DynamoDB Table Access" "aws dynamodb describe-table --table-name eks-chaos-guardian-runbook-index --profile eks-chaos-guardian"

# 2. Lambda Function Tests
echo -e "\n${YELLOW}=== LAMBDA FUNCTION TESTS ===${NC}"

# Test fault injection functions
test_lambda "eks-chaos-guardian-node-failure" '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' "Node Failure Injection (Dry Run)"
test_lambda "eks-chaos-guardian-pod-eviction" '{"cluster":"eks-chaos-guardian-autopilot","namespace":"default","dry_run":true}' "Pod Eviction (Dry Run)"
test_lambda "eks-chaos-guardian-network-latency" '{"cluster":"eks-chaos-guardian-autopilot","latency_ms":100,"dry_run":true}' "Network Latency (Dry Run)"
test_lambda "eks-chaos-guardian-api-throttling" '{"cluster":"eks-chaos-guardian-autopilot","throttle_rate":0.5,"dry_run":true}' "API Throttling (Dry Run)"

# Test detection functions
test_lambda "eks-chaos-guardian-cloudwatch-logs" '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc","limit":10}' "CloudWatch Logs Detection"
test_lambda "eks-chaos-guardian-cloudwatch-metrics" '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}' "CloudWatch Metrics Detection"

# Test execution functions
test_lambda "eks-chaos-guardian-k8s-operations" '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-deployment","patch":{"spec":{"replicas":3}},"dry_run":true}' "K8s Operations (Dry Run)"

# Test runbook management
test_lambda "eks-chaos-guardian-runbook-manager" '{"action":"search","search_criteria":{"failure_type":"oom_killed"}}' "Runbook Management"

# 3. Integration Tests
echo -e "\n${YELLOW}=== INTEGRATION TESTS ===${NC}"

# Test end-to-end workflow
echo -e "\n${BLUE}Testing End-to-End Workflow...${NC}"

# Deploy test application
echo "Deploying test application..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test application deployed${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Failed to deploy test application${NC}"
    ((TESTS_FAILED++))
fi

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/test-app

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test application ready${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Test application not ready${NC}"
    ((TESTS_FAILED++))
fi

# Test fault injection (dry run)
echo "Testing fault injection workflow..."
test_lambda "eks-chaos-guardian-node-failure" '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' "Fault Injection Workflow"

# Test detection
echo "Testing detection workflow..."
test_lambda "eks-chaos-guardian-cloudwatch-logs" '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc","limit":5}' "Detection Workflow"

# Test remediation
echo "Testing remediation workflow..."
test_lambda "eks-chaos-guardian-k8s-operations" '{"operation":"scale_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-app","patch":{"replicas":3},"dry_run":true}' "Remediation Workflow"

# 4. Runbook System Tests
echo -e "\n${YELLOW}=== RUNBOOK SYSTEM TESTS ===${NC}"

# Test runbook storage
echo "Testing runbook storage..."
test_lambda "eks-chaos-guardian-runbook-manager" '{"action":"store","runbook_data":{"title":"Test Runbook","description":"Test runbook for OOMKilled pods","failure_type":"oom_killed","severity":"high","steps":[{"type":"k8s_operation","config":{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource":"test-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"nginx","resources":{"requests":{"memory":"128Mi"},"limits":{"memory":"256Mi"}}}]}}}}}}]}}' "Runbook Storage"

# Test runbook retrieval
echo "Testing runbook retrieval..."
# Note: This would need the actual runbook ID from the previous test
test_lambda "eks-chaos-guardian-runbook-manager" '{"action":"search","search_criteria":{"failure_type":"oom_killed"}}' "Runbook Search"

# 5. Performance Tests
echo -e "\n${YELLOW}=== PERFORMANCE TESTS ===${NC}"

# Test concurrent Lambda invocations
echo "Testing concurrent Lambda invocations..."
for i in {1..5}; do
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"}}' "/tmp/response_$i.json" --profile eks-chaos-guardian &
done
wait

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Concurrent Lambda invocations successful${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Concurrent Lambda invocations failed${NC}"
    ((TESTS_FAILED++))
fi

# Clean up response files
rm -f /tmp/response_*.json

# 6. Cleanup
echo -e "\n${YELLOW}=== CLEANUP ===${NC}"

echo "Cleaning up test resources..."
kubectl delete deployment test-app

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test resources cleaned up${NC}"
else
    echo -e "${YELLOW}⚠️  Some test resources may not be cleaned up${NC}"
fi

# 7. Test Results Summary
echo -e "\n${YELLOW}================================================"
echo -e "TEST RESULTS SUMMARY${NC}"
echo -e "${YELLOW}================================================${NC}"

echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

total_tests=$((TESTS_PASSED + TESTS_FAILED))
if [ $total_tests -gt 0 ]; then
    success_rate=$((TESTS_PASSED * 100 / total_tests))
    echo -e "${BLUE}📊 Success Rate: $success_rate%${NC}"
fi

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! EKS Chaos Guardian is ready!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
