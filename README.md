# EKS Chaos Guardian - AWS AI Agent

An autonomous AI agent that performs intelligent chaos engineering on Amazon EKS clusters to ensure resilience and reliability.

## 🎯 Overview

EKS Chaos Guardian is an AWS-native agent that:
- **Injects** controlled faults into Amazon EKS
- **Detects** impact in near real-time via CloudWatch
- **Explains** root cause in plain English using Claude via Bedrock
- **Proposes** and executes safe fixes with guardrails
- **Verifies** recovery and stores successful runbooks for reuse

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack Bot     │    │  Bedrock         │    │  EKS Cluster    │
│   (Approvals)   │◄──►│  AgentCore       │◄──►│  (Target)       │
└─────────────────┘    │  (Claude)        │    └─────────────────┘
                       └──────────────────┘              │
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

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured
- Terraform >= 1.0
- Python 3.9+
- Slack workspace with webhook URL

### Platform Compatibility
✅ **Cross-platform support:**
- **Linux** (Ubuntu, CentOS, RHEL, etc.)
- **macOS** (Intel & Apple Silicon)
- **Windows** (PowerShell, WSL, Git Bash)

All scripts and commands are designed to work across platforms using standard tools like AWS CLI, Terraform, and Python.

### Deployment

```bash
# Clone and setup
git clone <your-repo>
cd eks-chaos-guardian

# Deploy infrastructure
make deploy

# Run health checks
./scripts/test-health.sh

# Run comprehensive tests
./scripts/test-all.sh

# Run interactive demo
./scripts/demo-scenario.sh
```

## 📁 Project Structure

```
eks-chaos-guardian/
├── scripts/               # Executable scripts
│   ├── test-health.sh
│   ├── test-all.sh
│   └── demo-scenario.sh
├── docs/                  # Documentation
│   ├── DEPLOYMENT.md
│   ├── PROJECT_SUMMARY.md
│   ├── TESTING_SUMMARY.md
│   ├── architecture.md
│   ├── testing-guide.md
│   └── cost-optimization.md
├── infra/                 # Terraform infrastructure
│   ├── cost-optimized.tf
│   ├── variables.tf
│   └── backend.tf
├── agent/                 # Bedrock AgentCore configuration
│   ├── agent-config.yaml
│   ├── tools/
│   └── prompts/
├── lambda/                # Lambda functions
│   ├── fault-injection/
│   ├── detection/
│   ├── execution/
│   ├── slack/
│   └── runbook/
├── demo/                  # Demo scenarios
│   └── scenarios/
├── ui/                    # Web dashboard
├── tests/                 # Test suite
├── Makefile              # Build automation
├── README.md             # Project overview
└── requirements.txt      # Python dependencies
```

## 🧪 Demo Scenarios

1. **OOMKilled** - Memory limit too low
2. **ImagePullBackOff** - Missing image pull secret
3. **Readiness Probe** - Misconfigured health checks
4. **Node Disk Pressure** - Node storage full
5. **PDB Blocking** - PodDisruptionBudget preventing rollout
6. **CoreDNS Failure** - DNS service disruption

## 🔧 Features

- **Autonomous Decision Making** using Claude via Bedrock AgentCore
- **Real-time Detection** via CloudWatch Logs Insights and Metrics
- **Safe Execution** with approval workflows and risk gates
- **Runbook Learning** - stores and reuses successful remediation patterns
- **Slack Integration** for notifications and approvals
- **Comprehensive Auditing** with S3 and DynamoDB storage

## 📊 KPIs

- Diagnosis ≤ 60s
- Plan generation ≤ 30s  
- Success rate ≥ 90% across scenarios
- Automated runbook reuse on repeated patterns

## 🛡️ Security

- Least-privilege IAM roles
- TLS encryption in transit
- S3 server-side encryption
- PII redaction before LLM processing

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
