# 🧪 EKS Chaos Guardian - Testing Summary

## 🎯 **How to Test Everything**

### **Quick Start Testing**

#### 1. **Health Check (5 minutes)**
```powershell
# Windows PowerShell
.\test-health.ps1

# Linux/Mac
./test-health.sh
```

#### 2. **Comprehensive Testing (15 minutes)**
```powershell
# Windows PowerShell
.\test-all.ps1

# Linux/Mac
./test-all.sh
```

#### 3. **Demo Scenarios (10 minutes each)**
```powershell
# Windows PowerShell
.\demo-scenario.ps1 oomkilled
.\demo-scenario.ps1 image-pull
.\demo-scenario.ps1 readiness
.\demo-scenario.ps1 crash-loop
.\demo-scenario.ps1 network
.\demo-scenario.ps1 api-throttle
.\demo-scenario.ps1 all

# Linux/Mac
./demo-scenario.sh oomkilled
./demo-scenario.sh image-pull
./demo-scenario.sh readiness
./demo-scenario.sh crash-loop
./demo-scenario.sh network
./demo-scenario.sh api-throttle
./demo-scenario.sh all
```

## 🔧 **Manual Testing Steps**

### **1. Infrastructure Testing**

#### Check AWS Resources
```bash
# Check EKS cluster
aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Check Lambda functions
aws lambda list-functions --profile eks-chaos-guardian | grep eks-chaos-guardian

# Check S3 bucket
aws s3 ls s3://eks-chaos-guardian-runbooks --profile eks-chaos-guardian

# Check DynamoDB table
aws dynamodb describe-table --table-name eks-chaos-guardian-runbook-index --profile eks-chaos-guardian
```

#### Check Kubernetes Access
```bash
# Get kubeconfig
aws eks update-kubeconfig --region us-east-1 --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Test cluster access
kubectl get nodes
kubectl get pods --all-namespaces
```

### **2. Lambda Function Testing**

#### Test Fault Injection Functions
```bash
# Node failure (dry run)
aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' response.json --profile eks-chaos-guardian

# Pod eviction (dry run)
aws lambda invoke --function-name eks-chaos-guardian-pod-eviction --payload '{"cluster":"eks-chaos-guardian-autopilot","namespace":"default","dry_run":true}' response.json --profile eks-chaos-guardian

# Network latency (dry run)
aws lambda invoke --function-name eks-chaos-guardian-network-latency --payload '{"cluster":"eks-chaos-guardian-autopilot","latency_ms":100,"dry_run":true}' response.json --profile eks-chaos-guardian

# API throttling (dry run)
aws lambda invoke --function-name eks-chaos-guardian-api-throttling --payload '{"cluster":"eks-chaos-guardian-autopilot","throttle_rate":0.5,"dry_run":true}' response.json --profile eks-chaos-guardian
```

#### Test Detection Functions
```bash
# CloudWatch Logs
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc","limit":10}' response.json --profile eks-chaos-guardian

# CloudWatch Metrics
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}' response.json --profile eks-chaos-guardian
```

#### Test Execution Functions
```bash
# K8s operations (dry run)
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-deployment","patch":{"spec":{"replicas":3}},"dry_run":true}' response.json --profile eks-chaos-guardian
```

#### Test Integration Functions
```bash
# Runbook management
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"search","search_criteria":{"failure_type":"oom_killed"}}' response.json --profile eks-chaos-guardian

# Slack bot (if configured)
# Test with Slack slash commands: /chaos help
```

### **3. End-to-End Testing**

#### Deploy Test Application
```bash
# Deploy test app
kubectl apply -f demo/scenarios/test-app.yaml

# Check deployment
kubectl get pods -l app=test-app
kubectl get services
kubectl get hpa
kubectl get pdb
```

#### Test Complete Workflow
```bash
# 1. Inject fault (dry run)
aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' response.json --profile eks-chaos-guardian

# 2. Detect impact
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc"}' response.json --profile eks-chaos-guardian

# 3. Execute remediation
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"scale_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-app","patch":{"replicas":5}}' response.json --profile eks-chaos-guardian
```

### **4. Web UI Testing**

#### Start Web UI
```bash
# Start web server
cd ui
python server.py

# Open browser to http://localhost:5000
```

#### Test Web Interface
- Navigate to dashboard
- Test fault injection buttons
- Check detection results
- Monitor cluster status

### **5. Slack Bot Testing**

#### Setup Slack App
1. Go to https://api.slack.com/apps
2. Create new app
3. Add slash commands: `/chaos`, `/status`, `/approve`
4. Add interactive components
5. Set request URL to your API Gateway endpoint
6. Install app to workspace

#### Test Slack Commands
```
/chaos help
/chaos node-failure eks-chaos-guardian-autopilot
/chaos detect-logs eks-chaos-guardian-autopilot
/status eks-chaos-guardian-autopilot
```

### **6. Runbook System Testing**

#### Test Runbook Storage
```bash
# Store a runbook
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"store","runbook_data":{"title":"Fix OOMKilled Pods","description":"Automated remediation for OOM killed pods","failure_type":"oom_killed","steps":[{"type":"k8s_operation","config":{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource":"my-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"main","resources":{"requests":{"memory":"512Mi"},"limits":{"memory":"1Gi"}}}]}}}}}}]}}' response.json --profile eks-chaos-guardian
```

#### Test Runbook Retrieval
```bash
# Search runbooks
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"search","search_criteria":{"failure_type":"oom_killed"}}' response.json --profile eks-chaos-guardian
```

## 🎬 **Demo Scenarios**

### **Scenario 1: OOMKilled Pods**
```bash
# Deploy memory-constrained app
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oom-test-app
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
        resources:
          requests:
            memory: "64Mi"
          limits:
            memory: "128Mi"  # Very low limit
        command: ["/bin/sh"]
        args: ["-c", "while true; do dd if=/dev/zero of=/tmp/memory bs=1M count=100; sleep 1; done"]
EOF

# Wait for OOMKilled
sleep 30
kubectl get pods -l app=oom-test-app

# Test detection
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /OOMKilled/ | sort @timestamp desc"}' response.json --profile eks-chaos-guardian

# Test remediation
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"oom-test-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"memory-hog","resources":{"requests":{"memory":"256Mi"},"limits":{"memory":"512Mi"}}}]}}}},"dry_run":true}' response.json --profile eks-chaos-guardian

# Cleanup
kubectl delete deployment oom-test-app
```

### **Scenario 2: ImagePullBackOff**
```bash
# Deploy with invalid image
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-pull-test
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
        image: invalid-image:latest  # This will fail
        ports:
        - containerPort: 80
EOF

# Wait for ImagePullBackOff
sleep 30
kubectl get pods -l app=image-pull-test

# Test detection
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ImagePullBackOff/ | sort @timestamp desc"}' response.json --profile eks-chaos-guardian

# Test remediation
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"rollout_restart","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"image-pull-test","dry_run":true}' response.json --profile eks-chaos-guardian

# Cleanup
kubectl delete deployment image-pull-test
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### Lambda Function Not Found
```bash
# Check if functions exist
aws lambda list-functions --profile eks-chaos-guardian | grep eks-chaos-guardian

# If missing, redeploy infrastructure
cd infra
terraform apply
```

#### EKS Cluster Not Accessible
```bash
# Check cluster status
aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian
```

#### S3/DynamoDB Access Issues
```bash
# Check permissions
aws s3api get-bucket-location --bucket eks-chaos-guardian-runbooks --profile eks-chaos-guardian
aws dynamodb describe-table --table-name eks-chaos-guardian-runbook-index --profile eks-chaos-guardian
```

## 📊 **Success Criteria**

### ✅ **Infrastructure Tests**
- [ ] EKS cluster accessible
- [ ] All Lambda functions deployed
- [ ] S3 bucket accessible
- [ ] DynamoDB table exists

### ✅ **Functionality Tests**
- [ ] Fault injection works (dry run)
- [ ] Detection functions return data
- [ ] K8s operations execute
- [ ] Slack bot responds
- [ ] Runbook system stores/retrieves

### ✅ **Integration Tests**
- [ ] End-to-end chaos workflow
- [ ] Slack approvals work
- [ ] Web UI displays data
- [ ] Runbook execution succeeds

### ✅ **Performance Tests**
- [ ] Functions respond < 30 seconds
- [ ] No memory leaks
- [ ] Concurrent execution works
- [ ] Error handling graceful

## 🎯 **Demo Preparation**

### **Pre-Demo Checklist**
- [ ] All infrastructure deployed
- [ ] Test application running
- [ ] Slack bot configured
- [ ] Web UI accessible
- [ ] Demo scenarios ready
- [ ] Backup plan prepared

### **Demo Script**
1. **Show Infrastructure**: EKS cluster, Lambda functions
2. **Deploy Test App**: Simple nginx deployment
3. **Inject Fault**: Node failure (dry run)
4. **Show Detection**: CloudWatch logs/metrics
5. **Execute Fix**: Scale deployment
6. **Show Learning**: Runbook storage
7. **Interactive Demo**: Slack bot commands

## 🔧 **Quick Test Commands**

```bash
# Quick health check
.\test-health.ps1

# Run all tests
.\test-all.ps1

# Demo scenario
.\demo-scenario.ps1 oomkilled
```

This comprehensive testing guide ensures your EKS Chaos Guardian is fully functional and ready for the hackathon demo!
