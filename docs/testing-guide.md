# EKS Chaos Guardian - Testing Guide

## 🧪 Complete Testing Strategy

### 1. **Infrastructure Testing**

#### Test AWS Infrastructure
```bash
# Check if infrastructure is deployed
cd infra
terraform plan  # Should show no changes if deployed correctly

# Verify EKS cluster
aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Check Lambda functions
aws lambda list-functions --profile eks-chaos-guardian | grep eks-chaos-guardian
```

#### Test EKS Cluster Connectivity
```bash
# Get kubeconfig
aws eks update-kubeconfig --region us-east-1 --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Test cluster access
kubectl get nodes
kubectl get pods --all-namespaces
```

### 2. **Lambda Function Testing**

#### Test Individual Lambda Functions
```bash
# Test fault injection functions
aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{"cluster":"eks-chaos-guardian-autopilot","dry_run":true}' response.json --profile eks-chaos-guardian

aws lambda invoke --function-name eks-chaos-guardian-pod-eviction --payload '{"cluster":"eks-chaos-guardian-autopilot","namespace":"default","dry_run":true}' response.json --profile eks-chaos-guardian

aws lambda invoke --function-name eks-chaos-guardian-network-latency --payload '{"cluster":"eks-chaos-guardian-autopilot","latency_ms":100,"dry_run":true}' response.json --profile eks-chaos-guardian

aws lambda invoke --function-name eks-chaos-guardian-api-throttling --payload '{"cluster":"eks-chaos-guardian-autopilot","throttle_rate":0.5,"dry_run":true}' response.json --profile eks-chaos-guardian
```

#### Test Detection Functions
```bash
# Test log detection
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc","limit":10}' response.json --profile eks-chaos-guardian

# Test metrics detection
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}' response.json --profile eks-chaos-guardian
```

#### Test Execution Functions
```bash
# Test K8s operations
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-deployment","patch":{"spec":{"replicas":3}},"dry_run":true}' response.json --profile eks-chaos-guardian
```

### 3. **Slack Bot Testing**

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

### 4. **Web UI Testing**

#### Start Web UI
```bash
# Start the web server
cd ui
python server.py

# Open browser to http://localhost:5000
```

#### Test Web Interface
- Navigate to dashboard
- Test fault injection buttons
- Check detection results
- Monitor cluster status

### 5. **End-to-End Testing**

#### Test Complete Chaos Engineering Workflow
```bash
# 1. Deploy test application
kubectl apply -f demo/scenarios/test-app.yaml

# 2. Inject fault
aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{"cluster":"eks-chaos-guardian-autopilot","dry_run":false}' response.json --profile eks-chaos-guardian

# 3. Detect impact
aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc"}' response.json --profile eks-chaos-guardian

# 4. Execute remediation
aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload '{"operation":"scale_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"test-app","patch":{"replicas":5}}' response.json --profile eks-chaos-guardian
```

### 6. **Runbook System Testing**

#### Test Runbook Storage
```bash
# Store a runbook
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"store","runbook_data":{"title":"Fix OOMKilled Pods","description":"Automated remediation for OOM killed pods","failure_type":"oom_killed","steps":[{"type":"k8s_operation","config":{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource":"my-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"main","resources":{"requests":{"memory":"512Mi"},"limits":{"memory":"1Gi"}}}]}}}}}}]}}' response.json --profile eks-chaos-guardian
```

#### Test Runbook Retrieval
```bash
# Get runbook by ID
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"retrieve","runbook_id":"<runbook-id>"}' response.json --profile eks-chaos-guardian

# Search runbooks
aws lambda invoke --function-name eks-chaos-guardian-runbook-manager --payload '{"action":"search","search_criteria":{"failure_type":"oom_killed"}}' response.json --profile eks-chaos-guardian
```

### 7. **Demo Scenarios Testing**

#### Test All 6 Demo Scenarios
```bash
# Run OOMKilled scenario
python demo/scenarios/oomkilled.py

# Run ImagePullBackOff scenario  
python demo/scenarios/image_pull_backoff.py

# Run Readiness Probe scenario
python demo/scenarios/readiness_probe.py
```

### 8. **Performance Testing**

#### Test Under Load
```bash
# Simulate high load
for i in {1..10}; do
  aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"}}' response$i.json --profile eks-chaos-guardian &
done
wait
```

### 9. **Security Testing**

#### Test Permissions
```bash
# Verify IAM roles
aws iam get-role --role-name eks-chaos-guardian-cluster-role --profile eks-chaos-guardian
aws iam get-role --role-name eks-chaos-guardian-node-group-role --profile eks-chaos-guardian

# Test S3 access
aws s3 ls s3://eks-chaos-guardian-runbooks --profile eks-chaos-guardian
```

### 10. **Monitoring and Observability**

#### Check CloudWatch Logs
```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/eks-chaos-guardian" --profile eks-chaos-guardian

# Get recent logs
aws logs filter-log-events --log-group-name "/aws/lambda/eks-chaos-guardian-bedrock-agent" --start-time $(date -d '1 hour ago' +%s)000 --profile eks-chaos-guardian
```

#### Check Metrics
```bash
# View CloudWatch metrics
aws cloudwatch list-metrics --namespace "AWS/Lambda" --metric-name "Invocations" --profile eks-chaos-guardian
```

## 🚨 **Troubleshooting Common Issues**

### Lambda Function Not Found
```bash
# Check if functions exist
aws lambda list-functions --profile eks-chaos-guardian | grep eks-chaos-guardian

# If missing, redeploy infrastructure
cd infra
terraform apply
```

### EKS Cluster Not Accessible
```bash
# Check cluster status
aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian
```

### Slack Bot Not Responding
1. Check API Gateway endpoint
2. Verify Slack app configuration
3. Check Lambda function logs
4. Test with curl

### S3/DynamoDB Access Issues
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

### Pre-Demo Checklist
- [ ] All infrastructure deployed
- [ ] Test application running
- [ ] Slack bot configured
- [ ] Web UI accessible
- [ ] Demo scenarios ready
- [ ] Backup plan prepared

### Demo Script
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
./test-health.sh

# Run all tests
./test-all.sh

# Demo scenario
./demo-scenario.sh oomkilled
```

This comprehensive testing guide ensures your EKS Chaos Guardian is fully functional and ready for the hackathon demo!
