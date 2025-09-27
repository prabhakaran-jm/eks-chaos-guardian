#!/bin/bash
# Deploy EKS Chaos Guardian UI to AWS Amplify
# Perfect for hackathon demos - simple, reliable, AWS-native

echo "🚀 Deploying EKS Chaos Guardian UI to AWS Amplify..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    echo "   Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity --profile eks-chaos-guardian &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    echo "   Or set AWS_PROFILE=eks-chaos-guardian"
    exit 1
fi

echo "✅ AWS CLI configured successfully"

# Create a simple static version for Amplify
echo "📝 Creating static version for Amplify..."

# Create index.html that works without server
cat > index_static.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EKS Chaos Guardian - AWS AI Agent Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .demo-section { background: white; border-radius: 15px; padding: 30px; margin: 20px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .demo-section h2 { color: #333; margin-bottom: 20px; font-size: 1.8em; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .feature-card { background: #f8f9fa; border-radius: 10px; padding: 20px; border-left: 4px solid #667eea; }
        .feature-card h3 { color: #667eea; margin-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .status-card { background: #e8f5e8; border-radius: 8px; padding: 15px; text-align: center; border: 2px solid #28a745; }
        .status-card h4 { color: #28a745; margin-bottom: 5px; }
        .tech-stack { background: #f0f8ff; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .tech-stack h3 { color: #0066cc; margin-bottom: 15px; }
        .tech-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .tech-item { background: #0066cc; color: white; padding: 8px 16px; border-radius: 20px; font-size: 0.9em; }
        .demo-video { text-align: center; margin: 30px 0; }
        .demo-video iframe { border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .github-link { text-align: center; margin: 20px 0; }
        .github-link a { display: inline-block; background: #333; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; transition: background 0.3s; }
        .github-link a:hover { background: #555; }
        .aws-badge { display: inline-block; background: #ff9900; color: white; padding: 5px 15px; border-radius: 15px; font-size: 0.8em; font-weight: bold; margin-left: 10px; }
        @media (max-width: 768px) { .container { padding: 10px; } .header h1 { font-size: 2em; } .feature-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ EKS Chaos Guardian</h1>
            <p>AI-Powered Kubernetes Resilience Testing Platform</p>
            <span class="aws-badge">AWS AI Agent Hackathon 2024</span>
        </div>

        <div class="demo-section">
            <h2>🎯 Hackathon Demo Overview</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🤖 AI Agent Architecture</h3>
                    <p>Built with Amazon Bedrock AgentCore using Claude 3.5 Sonnet for intelligent decision-making and autonomous remediation.</p>
                </div>
                <div class="feature-card">
                    <h3>⚡ Chaos Engineering</h3>
                    <p>Automated fault injection into EKS clusters with real-time impact detection and root cause analysis.</p>
                </div>
                <div class="feature-card">
                    <h3>🔧 Auto-Remediation</h3>
                    <p>AI-driven fix proposals with human approval workflows and automated verification of recovery.</p>
                </div>
                <div class="feature-card">
                    <h3>📚 Learning System</h3>
                    <p>Stores successful remediation patterns as reusable runbooks for faster incident response.</p>
                </div>
            </div>
        </div>

        <div class="demo-section">
            <h2>🚀 Live Demo Scenarios</h2>
            <div class="status-grid">
                <div class="status-card">
                    <h4>Node Failure</h4>
                    <p>Simulate worker node termination and auto-recovery</p>
                </div>
                <div class="status-card">
                    <h4>Pod Eviction</h4>
                    <p>Test pod disruption budgets and rescheduling</p>
                </div>
                <div class="status-card">
                    <h4>Network Latency</h4>
                    <p>Inject network delays and measure impact</p>
                </div>
                <div class="status-card">
                    <h4>API Throttling</h4>
                    <p>Simulate rate limiting and observe behavior</p>
                </div>
                <div class="status-card">
                    <h4>OOMKilled</h4>
                    <p>Memory pressure testing with auto-scaling</p>
                </div>
                <div class="status-card">
                    <h4>ImagePullBackOff</h4>
                    <p>Container registry issues and resolution</p>
                </div>
            </div>
        </div>

        <div class="demo-section">
            <h2>🛠️ AWS Technology Stack</h2>
            <div class="tech-stack">
                <h3>Core AI Services</h3>
                <div class="tech-list">
                    <span class="tech-item">Amazon Bedrock AgentCore</span>
                    <span class="tech-item">Claude 3.5 Sonnet</span>
                    <span class="tech-item">Amazon Bedrock</span>
                </div>
                
                <h3>Infrastructure & Compute</h3>
                <div class="tech-list">
                    <span class="tech-item">Amazon EKS Autopilot</span>
                    <span class="tech-item">AWS Lambda</span>
                    <span class="tech-item">Amazon EC2</span>
                </div>
                
                <h3>Storage & Database</h3>
                <div class="tech-list">
                    <span class="tech-item">Amazon S3</span>
                    <span class="tech-item">Amazon DynamoDB</span>
                </div>
                
                <h3>Monitoring & Integration</h3>
                <div class="tech-list">
                    <span class="tech-item">Amazon CloudWatch</span>
                    <span class="tech-item">Amazon API Gateway</span>
                    <span class="tech-item">Slack Integration</span>
                </div>
            </div>
        </div>

        <div class="demo-section">
            <h2>📊 Demo Metrics & KPIs</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>⚡ Performance</h3>
                    <p>• Detection + Diagnosis: ≤ 60 seconds<br>• Plan Generation: ≤ 30 seconds<br>• Recovery Verification: 2-5 minutes</p>
                </div>
                <div class="feature-card">
                    <h3>🎯 Success Rate</h3>
                    <p>• 90%+ success rate across all scenarios<br>• Automated runbook reuse<br>• Human approval for high-risk actions</p>
                </div>
                <div class="feature-card">
                    <h3>💰 Cost Optimization</h3>
                    <p>• EKS Autopilot for cost efficiency<br>• Serverless Lambda functions<br>• Pay-per-use model</p>
                </div>
            </div>
        </div>

        <div class="demo-section">
            <h2>🎥 Demo Video</h2>
            <div class="demo-video">
                <p><strong>3-Minute Live Demo:</strong> Watch the EKS Chaos Guardian in action</p>
                <p><em>Video will be embedded here for the hackathon submission</em></p>
            </div>
        </div>

        <div class="demo-section">
            <h2>🔗 Repository & Documentation</h2>
            <div class="github-link">
                <a href="https://github.com/yourusername/eks-chaos-guardian" target="_blank">
                    📁 View Source Code on GitHub
                </a>
            </div>
            <p style="text-align: center; color: #666; margin-top: 20px;">
                Complete implementation with Terraform infrastructure, Lambda functions, and Bedrock AgentCore configuration
            </p>
        </div>
    </div>

    <script>
        // Simple demo interactivity
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🛡️ EKS Chaos Guardian Demo Loaded');
            
            // Add click effects to status cards
            const statusCards = document.querySelectorAll('.status-card');
            statusCards.forEach(card => {
                card.addEventListener('click', function() {
                    this.style.transform = 'scale(1.05)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                    }, 200);
                });
            });
        });
    </script>
</body>
</html>
EOF

echo "✅ Static HTML created"

# Create Amplify configuration
cat > amplify.yml << 'EOF'
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - echo "Building EKS Chaos Guardian UI for AWS Amplify"
    build:
      commands:
        - echo "Static site - no build required"
        - cp index_static.html index.html
  artifacts:
    baseDirectory: /
    files:
      - '**/*'
EOF

echo "✅ Amplify configuration created"

echo ""
echo "🚀 Ready to deploy to AWS Amplify!"
echo ""
echo "📋 Next steps:"
echo "1. Go to AWS Amplify Console: https://console.aws.amazon.com/amplify/"
echo "2. Click 'Host web app'"
echo "3. Choose 'Deploy without Git provider'"
echo "4. Upload the contents of this directory"
echo "5. App name: eks-chaos-guardian-demo"
echo "6. Environment: main"
echo "7. Build settings: amplify.yml (already created)"
echo ""
echo "🌐 After deployment:"
echo "1. Go to 'Domain management' in Amplify"
echo "2. Add custom domain: chaos-guardian.cloudaimldeveops.com"
echo "3. Request SSL certificate (free with AWS Certificate Manager)"
echo "4. Update your domain's DNS records as instructed"
echo ""
echo "💰 Estimated cost: $1-5/month (AWS Amplify free tier + domain)"
echo "⏱️  Deployment time: 5-10 minutes"
echo "🎯 Perfect for hackathon demo!"
