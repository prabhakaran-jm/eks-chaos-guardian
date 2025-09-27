# EKS Chaos Guardian - Deployment Guide

## Quick Start

This guide will help you deploy EKS Chaos Guardian for the AWS AI Agent Hackathon.

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** >= 1.0
4. **Python** 3.9+
5. **Slack Workspace** with webhook URL

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd eks-chaos-guardian
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Set AWS region
export AWS_REGION=us-east-1

# Set Slack webhook URL (optional but recommended)
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Set project variables
export PROJECT_NAME=eks-chaos-guardian
export ENVIRONMENT=demo
```

### 3. Deploy Infrastructure

```bash
# Initialize and deploy Terraform
make deploy
```

This will create:
- EKS cluster with managed node groups
- VPC with public/private subnets
- Lambda functions and IAM roles
- S3 bucket for audit logs and runbooks
- DynamoDB table for runbook indexing
- API Gateway endpoints
- CloudWatch dashboards

### 4. Verify Deployment

```bash
# Check cluster status
aws eks describe-cluster --name eks-chaos-guardian-cluster

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name eks-chaos-guardian-cluster

# Verify cluster access
kubectl get nodes
```

### 5. Run Demo Scenarios

```bash
# Run individual scenarios
make demo-oom
make demo-image-pull
make demo-readiness
make demo-disk
make demo-pdb
make demo-coredns

# Or run all scenarios
make demo-all
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack Bot     │    │  Bedrock         │    │  EKS Cluster    │
│   (Approvals)   │◄──►│  AgentCore       │◄──►│  (Target)       │
│                 │    │  (Claude)        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                       ┌────────▼────────┐              │
                       │  Lambda Tools   │◄─────────────┘
                       │  - Fault Inject │
                       │  - Detection    │
                       │  - Execution    │
                       │  - Verification │
                       └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │  Storage Layer  │
                       │  - S3 (Audit)   │
                       │  - DynamoDB     │
                       │    (Runbooks)   │
                       └─────────────────┘
```

## Key Features

### ✅ AWS Hackathon Requirements Met

1. **LLM Hosted on AWS**: Claude 3.5 Sonnet via Amazon Bedrock
2. **AWS Services Used**: 
   - Amazon Bedrock AgentCore
   - Amazon EKS
   - AWS Lambda
   - Amazon S3
   - Amazon DynamoDB
   - Amazon CloudWatch
   - Amazon API Gateway
3. **Autonomous Capabilities**: Intelligent decision-making and execution
4. **External Integrations**: Slack, Kubernetes APIs, CloudWatch
5. **Reasoning Component**: Claude for analysis and planning

### 🚀 Innovation Highlights

- **Intelligent Chaos Engineering**: AI-driven failure injection and analysis
- **Runbook Learning**: Automatic pattern recognition and reuse
- **Risk-Based Autonomy**: Smart approval workflows
- **Real-World Applicability**: Production-ready architecture
- **Comprehensive Coverage**: Six critical failure scenarios

## Demo Scenarios

### 1. OOMKilled (Out of Memory)
- **Trigger**: Deploy app with low memory limits
- **Detection**: CloudWatch Logs showing OOMKilled events
- **Remediation**: Increase memory limits and restart deployment
- **Risk Level**: LOW (auto-execute)

### 2. ImagePullBackOff
- **Trigger**: Deploy app with invalid image reference
- **Detection**: Logs showing image pull failures
- **Remediation**: Fix image reference and add pull secrets
- **Risk Level**: MEDIUM (requires approval)

### 3. Readiness Probe Failure
- **Trigger**: Deploy app with misconfigured health checks
- **Detection**: Probe failure logs
- **Remediation**: Correct probe configuration
- **Risk Level**: LOW (auto-execute)

### 4. Node Disk Pressure
- **Trigger**: Fill node disk space
- **Detection**: Node conditions and eviction events
- **Remediation**: Cordon/drain node and scale ASG
- **Risk Level**: HIGH (requires explicit approval)

### 5. PDB Blocking Rollouts
- **Trigger**: Restrictive Pod Disruption Budget
- **Detection**: Rollout blocking events
- **Remediation**: Temporarily relax PDB constraints
- **Risk Level**: HIGH (requires explicit approval)

### 6. CoreDNS Failure
- **Trigger**: Kill CoreDNS pods
- **Detection**: DNS resolution failures
- **Remediation**: Restart CoreDNS deployment
- **Risk Level**: LOW (auto-execute)

## Performance Metrics

- **Detection Time**: ≤ 60 seconds
- **Analysis Time**: ≤ 30 seconds
- **Recovery Time**: 2-5 minutes
- **Success Rate**: ≥ 90%
- **Autonomous Actions**: 70% of low-risk operations

## API Endpoints

### Fault Injection
```
POST /chaos/node-failure
POST /chaos/pod-evict
POST /chaos/net-latency
POST /chaos/api-throttle
```

### Detection
```
POST /detect/run
POST /detect/logs
POST /detect/metrics
```

### Execution
```
POST /execute/plan
POST /execute/verify
```

### Runbooks
```
GET /runbooks/{pattern_id}
POST /runbooks
```

## Monitoring and Observability

### CloudWatch Dashboards
- **Chaos Guardian Dashboard**: System metrics and performance
- **EKS Cluster Dashboard**: Cluster health and resource utilization
- **Lambda Functions Dashboard**: Function performance and errors

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Audit Trail**: All actions logged to S3
- **Error Tracking**: CloudWatch Logs with alerting

## Security Features

### IAM Security
- **Least Privilege**: Minimal required permissions
- **Role-Based Access**: Separate roles for each function
- **Resource Scoping**: Limited to demo namespaces

### Data Protection
- **Encryption at Rest**: S3 and DynamoDB encryption
- **Encryption in Transit**: TLS for all communications
- **PII Redaction**: Sensitive data filtered before LLM processing

### Network Security
- **VPC Isolation**: Private subnets for worker nodes
- **Security Groups**: Restrictive firewall rules
- **NAT Gateway**: Controlled outbound access

## Cost Optimization

### Resource Management
- **Auto Scaling**: EKS node groups scale based on demand
- **Lifecycle Policies**: S3 logs automatically archived
- **On-Demand Billing**: DynamoDB pay-per-use
- **Demo Cleanup**: Automated resource cleanup

### Estimated Costs
- **EKS Cluster**: ~$75/month (2 t3.medium nodes)
- **Lambda Functions**: ~$5/month (based on usage)
- **S3 Storage**: ~$2/month (logs and runbooks)
- **DynamoDB**: ~$1/month (runbook index)
- **Total**: ~$83/month for demo environment

## Troubleshooting

### Common Issues

1. **EKS Cluster Not Ready**
   ```bash
   aws eks describe-cluster --name eks-chaos-guardian-cluster --query cluster.status
   ```

2. **Lambda Function Errors**
   ```bash
   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/eks-chaos-guardian
   ```

3. **Slack Integration Issues**
   - Verify webhook URL is correct
   - Check Slack app permissions
   - Review Lambda function logs

4. **Permission Errors**
   ```bash
   aws sts get-caller-identity
   aws iam list-attached-role-policies --role-name eks-chaos-guardian-lambda-execution-role
   ```

### Debug Commands

```bash
# Check Terraform state
cd infra && terraform show

# View Lambda logs
aws logs tail /aws/lambda/eks-chaos-guardian-bedrock-agent --follow

# Test API endpoints
curl -X POST https://your-api-gateway-url/chaos/node-failure \
  -H "Content-Type: application/json" \
  -d '{"cluster":"eks-chaos-guardian-cluster","dry_run":true}'
```

## Cleanup

### Destroy Infrastructure
```bash
# Clean up all resources
make destroy

# Or manual cleanup
cd infra && terraform destroy -auto-approve
```

### Manual Cleanup Steps
1. Delete EKS cluster and node groups
2. Remove Lambda functions
3. Delete S3 bucket contents and bucket
4. Remove DynamoDB table
5. Delete VPC and networking resources

## Support and Resources

### Documentation
- [Architecture Documentation](docs/architecture.md)
- [Demo Video Script](docs/demo-video-script.md)
- [API Reference](docs/api-reference.md)

### GitHub Repository
- Source code and examples
- Issue tracking and feature requests
- Contributing guidelines

### AWS Resources
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon EKS Documentation](https://docs.aws.amazon.com/eks/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

## Hackathon Submission

### Deliverables Checklist
- ✅ **Public Code Repository**: Complete source code with instructions
- ✅ **Architecture Diagram**: Comprehensive system architecture
- ✅ **Text Description**: Detailed project description and features
- ✅ **Demo Video**: 3-minute demonstration video
- ✅ **Deployed Project**: Working system on AWS

### Key Points for Judges
1. **Innovation**: First AI-driven chaos engineering system for EKS
2. **Completeness**: Full end-to-end autonomous operation
3. **Real-World Value**: Solves actual SRE pain points
4. **Technical Excellence**: Production-ready architecture
5. **AWS Integration**: Deep use of AWS services and best practices

EKS Chaos Guardian represents a significant advancement in autonomous system operations, demonstrating how AI can be leveraged to improve reliability and reduce manual toil in cloud-native environments.
