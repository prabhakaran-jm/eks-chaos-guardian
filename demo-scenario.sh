#!/bin/bash

# EKS Chaos Guardian - Demo Scenario Script
# Runs specific demo scenarios to showcase the system

echo "🎬 EKS Chaos Guardian - Demo Scenarios"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${YELLOW}Usage: $0 <scenario>${NC}"
    echo -e "\n${BLUE}Available scenarios:${NC}"
    echo "  oomkilled      - OOMKilled pod scenario"
    echo "  image-pull      - ImagePullBackOff scenario"
    echo "  readiness      - Readiness probe failure scenario"
    echo "  crash-loop      - CrashLoopBackOff scenario"
    echo "  network         - Network latency scenario"
    echo "  api-throttle    - API throttling scenario"
    echo "  all            - Run all scenarios"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 oomkilled"
    echo "  $0 all"
}

# Function to run scenario
run_scenario() {
    local scenario="$1"
    
    echo -e "\n${PURPLE}🎬 Running Scenario: $scenario${NC}"
    echo "=================================="
    
    case $scenario in
        "oomkilled")
            run_oomkilled_scenario
            ;;
        "image-pull")
            run_image_pull_scenario
            ;;
        "readiness")
            run_readiness_scenario
            ;;
        "crash-loop")
            run_crash_loop_scenario
            ;;
        "network")
            run_network_scenario
            ;;
        "api-throttle")
            run_api_throttle_scenario
            ;;
        "all")
            run_all_scenarios
            ;;
        *)
            echo -e "${RED}❌ Unknown scenario: $scenario${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# OOMKilled Scenario
run_oomkilled_scenario() {
    echo -e "\n${BLUE}📋 OOMKilled Pod Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Deploying a memory-constrained application"
    echo "2. Triggering OOMKilled pods"
    echo "3. Detecting the issue via logs"
    echo "4. Applying automated remediation"
    
    echo -e "\n${YELLOW}Step 1: Deploying memory-constrained application...${NC}"
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oom-test-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oom-test-app
  template:
    metadata:
      labels:
        app: oom-test-app
    spec:
      containers:
      - name: memory-hog
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"  # Very low limit to trigger OOM
            cpu: "100m"
        command: ["/bin/sh"]
        args: ["-c", "while true; do dd if=/dev/zero of=/tmp/memory bs=1M count=100; sleep 1; done"]
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Application deployed${NC}"
    else
        echo -e "${RED}❌ Failed to deploy application${NC}"
        return 1
    fi
    
    echo -e "\n${YELLOW}Step 2: Waiting for OOMKilled pods...${NC}"
    sleep 30
    
    echo -e "\n${YELLOW}Step 3: Detecting OOMKilled pods...${NC}"
    kubectl get pods -l app=oom-test-app
    
    echo -e "\n${YELLOW}Step 4: Testing log detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /OOMKilled/ | sort @timestamp desc","limit":10}' /tmp/oom_logs.json --profile eks-chaos-guardian
    
    if [ -f "/tmp/oom_logs.json" ]; then
        echo -e "${GREEN}✅ Log detection completed${NC}"
        cat /tmp/oom_logs.json | jq '.body' 2>/dev/null || cat /tmp/oom_logs.json
    fi
    
    echo -e "\n${YELLOW}Step 5: Testing remediation (dry run)...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"oom-test-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"memory-hog","resources":{"requests":{"memory":"256Mi"},"limits":{"memory":"512Mi"}}}]}}}},"dry_run":true}' /tmp/oom_fix.json --profile eks-chaos-guardian
    
    if [ -f "/tmp/oom_fix.json" ]; then
        echo -e "${GREEN}✅ Remediation plan generated${NC}"
        cat /tmp/oom_fix.json | jq '.body' 2>/dev/null || cat /tmp/oom_fix.json
    fi
    
    echo -e "\n${YELLOW}Step 6: Cleaning up...${NC}"
    kubectl delete deployment oom-test-app
    rm -f /tmp/oom_*.json
    
    echo -e "${GREEN}✅ OOMKilled scenario completed${NC}"
}

# ImagePullBackOff Scenario
run_image_pull_scenario() {
    echo -e "\n${BLUE}📋 ImagePullBackOff Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Deploying with invalid image"
    echo "2. Detecting ImagePullBackOff"
    echo "3. Applying remediation"
    
    echo -e "\n${YELLOW}Step 1: Deploying with invalid image...${NC}"
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-pull-test
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: image-pull-test
  template:
    metadata:
      labels:
        app: image-pull-test
    spec:
      containers:
      - name: invalid-image
        image: invalid-image:latest  # This will fail to pull
        ports:
        - containerPort: 80
EOF
    
    echo -e "\n${YELLOW}Step 2: Waiting for ImagePullBackOff...${NC}"
    sleep 30
    
    echo -e "\n${YELLOW}Step 3: Checking pod status...${NC}"
    kubectl get pods -l app=image-pull-test
    
    echo -e "\n${YELLOW}Step 4: Testing detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ImagePullBackOff/ | sort @timestamp desc","limit":10}' /tmp/image_pull_logs.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 5: Testing remediation...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"rollout_restart","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"image-pull-test","dry_run":true}' /tmp/image_pull_fix.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 6: Cleaning up...${NC}"
    kubectl delete deployment image-pull-test
    rm -f /tmp/image_pull_*.json
    
    echo -e "${GREEN}✅ ImagePullBackOff scenario completed${NC}"
}

# Readiness Probe Scenario
run_readiness_scenario() {
    echo -e "\n${BLUE}📋 Readiness Probe Failure Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Deploying with failing readiness probe"
    echo "2. Detecting readiness probe failures"
    echo "3. Applying remediation"
    
    echo -e "\n${YELLOW}Step 1: Deploying with failing readiness probe...${NC}"
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: readiness-test
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: readiness-test
  template:
    metadata:
      labels:
        app: readiness-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /nonexistent  # This will fail
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
EOF
    
    echo -e "\n${YELLOW}Step 2: Waiting for readiness probe failures...${NC}"
    sleep 30
    
    echo -e "\n${YELLOW}Step 3: Checking pod status...${NC}"
    kubectl get pods -l app=readiness-test
    
    echo -e "\n${YELLOW}Step 4: Testing detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /Readiness probe failed/ | sort @timestamp desc","limit":10}' /tmp/readiness_logs.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 5: Testing remediation...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"readiness-test","patch":{"spec":{"template":{"spec":{"containers":[{"name":"nginx","readinessProbe":{"httpGet":{"path":"/","port":80},"initialDelaySeconds":5,"periodSeconds":5}}]}}}},"dry_run":true}' /tmp/readiness_fix.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 6: Cleaning up...${NC}"
    kubectl delete deployment readiness-test
    rm -f /tmp/readiness_*.json
    
    echo -e "${GREEN}✅ Readiness probe scenario completed${NC}"
}

# CrashLoopBackOff Scenario
run_crash_loop_scenario() {
    echo -e "\n${BLUE}📋 CrashLoopBackOff Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Deploying with crashing container"
    echo "2. Detecting CrashLoopBackOff"
    echo "3. Applying remediation"
    
    echo -e "\n${YELLOW}Step 1: Deploying crashing application...${NC}"
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crash-test
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: crash-test
  template:
    metadata:
      labels:
        app: crash-test
    spec:
      containers:
      - name: crash-container
        image: nginx:1.20
        command: ["/bin/sh"]
        args: ["-c", "exit 1"]  # This will crash immediately
EOF
    
    echo -e "\n${YELLOW}Step 2: Waiting for CrashLoopBackOff...${NC}"
    sleep 30
    
    echo -e "\n${YELLOW}Step 3: Checking pod status...${NC}"
    kubectl get pods -l app=crash-test
    
    echo -e "\n${YELLOW}Step 4: Testing detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /CrashLoopBackOff/ | sort @timestamp desc","limit":10}' /tmp/crash_logs.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 5: Testing remediation...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"rollout_restart","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"crash-test","dry_run":true}' /tmp/crash_fix.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 6: Cleaning up...${NC}"
    kubectl delete deployment crash-test
    rm -f /tmp/crash_*.json
    
    echo -e "${GREEN}✅ CrashLoopBackOff scenario completed${NC}"
}

# Network Latency Scenario
run_network_scenario() {
    echo -e "\n${BLUE}📋 Network Latency Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Injecting network latency"
    echo "2. Detecting performance issues"
    echo "3. Applying remediation"
    
    echo -e "\n${YELLOW}Step 1: Testing network latency injection (dry run)...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-network-latency --payload '{"cluster":"eks-chaos-guardian-autopilot","latency_ms":100,"duration_seconds":60,"dry_run":true}' /tmp/network_latency.json --profile eks-chaos-guardian
    
    if [ -f "/tmp/network_latency.json" ]; then
        echo -e "${GREEN}✅ Network latency injection planned${NC}"
        cat /tmp/network_latency.json | jq '.body' 2>/dev/null || cat /tmp/network_latency.json
    fi
    
    echo -e "\n${YELLOW}Step 2: Testing metrics detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}' /tmp/network_metrics.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 3: Cleaning up...${NC}"
    rm -f /tmp/network_*.json
    
    echo -e "${GREEN}✅ Network latency scenario completed${NC}"
}

# API Throttling Scenario
run_api_throttle_scenario() {
    echo -e "\n${BLUE}📋 API Throttling Scenario${NC}"
    echo "This scenario demonstrates:"
    echo "1. Injecting API throttling"
    echo "2. Detecting throttling effects"
    echo "3. Applying remediation"
    
    echo -e "\n${YELLOW}Step 1: Testing API throttling injection (dry run)...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-api-throttling --payload '{"cluster":"eks-chaos-guardian-autopilot","throttle_rate":0.5,"duration_seconds":60,"dry_run":true}' /tmp/api_throttle.json --profile eks-chaos-guardian
    
    if [ -f "/tmp/api_throttle.json" ]; then
        echo -e "${GREEN}✅ API throttling injection planned${NC}"
        cat /tmp/api_throttle.json | jq '.body' 2>/dev/null || cat /tmp/api_throttle.json
    fi
    
    echo -e "\n${YELLOW}Step 2: Testing metrics detection...${NC}"
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}' /tmp/api_metrics.json --profile eks-chaos-guardian
    
    echo -e "\n${YELLOW}Step 3: Cleaning up...${NC}"
    rm -f /tmp/api_*.json
    
    echo -e "${GREEN}✅ API throttling scenario completed${NC}"
}

# Run All Scenarios
run_all_scenarios() {
    echo -e "\n${PURPLE}🎬 Running All Demo Scenarios${NC}"
    echo "=================================="
    
    run_oomkilled_scenario
    run_image_pull_scenario
    run_readiness_scenario
    run_crash_loop_scenario
    run_network_scenario
    run_api_throttle_scenario
    
    echo -e "\n${GREEN}🎉 All demo scenarios completed!${NC}"
}

# Main execution
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq is not installed. Some output formatting may not work properly.${NC}"
    echo "Install jq with: sudo apt-get install jq (Ubuntu) or brew install jq (macOS)"
fi

# Run the specified scenario
run_scenario "$1"
