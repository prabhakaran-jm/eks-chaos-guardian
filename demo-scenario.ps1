# EKS Chaos Guardian - Demo Scenario Script (PowerShell)
# Runs specific demo scenarios to showcase the system

param(
    [Parameter(Mandatory=$true)]
    [string]$Scenario
)

Write-Host "🎬 EKS Chaos Guardian - Demo Scenarios" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\demo-scenario.ps1 <scenario>" -ForegroundColor Yellow
    Write-Host "`nAvailable scenarios:" -ForegroundColor Blue
    Write-Host "  oomkilled      - OOMKilled pod scenario"
    Write-Host "  image-pull      - ImagePullBackOff scenario"
    Write-Host "  readiness      - Readiness probe failure scenario"
    Write-Host "  crash-loop      - CrashLoopBackOff scenario"
    Write-Host "  network         - Network latency scenario"
    Write-Host "  api-throttle    - API throttling scenario"
    Write-Host "  all            - Run all scenarios"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Blue
    Write-Host "  .\demo-scenario.ps1 oomkilled"
    Write-Host "  .\demo-scenario.ps1 all"
}

# Function to run scenario
function Run-Scenario {
    param($scenario)
    
    Write-Host "`n🎬 Running Scenario: $scenario" -ForegroundColor Magenta
    Write-Host "==================================" -ForegroundColor Magenta
    
    switch ($scenario) {
        "oomkilled" { Run-OOMKilledScenario }
        "image-pull" { Run-ImagePullScenario }
        "readiness" { Run-ReadinessScenario }
        "crash-loop" { Run-CrashLoopScenario }
        "network" { Run-NetworkScenario }
        "api-throttle" { Run-APIThrottleScenario }
        "all" { Run-AllScenarios }
        default {
            Write-Host "❌ Unknown scenario: $scenario" -ForegroundColor Red
            Show-Usage
            exit 1
        }
    }
}

# OOMKilled Scenario
function Run-OOMKilledScenario {
    Write-Host "`n📋 OOMKilled Pod Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Deploying a memory-constrained application"
    Write-Host "2. Triggering OOMKilled pods"
    Write-Host "3. Detecting the issue via logs"
    Write-Host "4. Applying automated remediation"
    
    Write-Host "`nStep 1: Deploying memory-constrained application..." -ForegroundColor Yellow
    
    $deploymentYaml = @"
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
"@
    
    $deploymentYaml | kubectl apply -f -
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Application deployed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to deploy application" -ForegroundColor Red
        return
    }
    
    Write-Host "`nStep 2: Waiting for OOMKilled pods..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host "`nStep 3: Detecting OOMKilled pods..." -ForegroundColor Yellow
    kubectl get pods -l app=oom-test-app
    
    Write-Host "`nStep 4: Testing log detection..." -ForegroundColor Yellow
    $payload = '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /OOMKilled/ | sort @timestamp desc","limit":10}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload $payload oom_logs.json --profile eks-chaos-guardian
    
    if (Test-Path "oom_logs.json") {
        Write-Host "✅ Log detection completed" -ForegroundColor Green
        Get-Content oom_logs.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    
    Write-Host "`nStep 5: Testing remediation (dry run)..." -ForegroundColor Yellow
    $remediationPayload = '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"oom-test-app","patch":{"spec":{"template":{"spec":{"containers":[{"name":"memory-hog","resources":{"requests":{"memory":"256Mi"},"limits":{"memory":"512Mi"}}}]}}}},"dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload $remediationPayload oom_fix.json --profile eks-chaos-guardian
    
    if (Test-Path "oom_fix.json") {
        Write-Host "✅ Remediation plan generated" -ForegroundColor Green
        Get-Content oom_fix.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    
    Write-Host "`nStep 6: Cleaning up..." -ForegroundColor Yellow
    kubectl delete deployment oom-test-app
    Remove-Item -Path "oom_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ OOMKilled scenario completed" -ForegroundColor Green
}

# ImagePullBackOff Scenario
function Run-ImagePullScenario {
    Write-Host "`n📋 ImagePullBackOff Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Deploying with invalid image"
    Write-Host "2. Detecting ImagePullBackOff"
    Write-Host "3. Applying remediation"
    
    Write-Host "`nStep 1: Deploying with invalid image..." -ForegroundColor Yellow
    
    $deploymentYaml = @"
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
"@
    
    $deploymentYaml | kubectl apply -f -
    
    Write-Host "`nStep 2: Waiting for ImagePullBackOff..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host "`nStep 3: Checking pod status..." -ForegroundColor Yellow
    kubectl get pods -l app=image-pull-test
    
    Write-Host "`nStep 4: Testing detection..." -ForegroundColor Yellow
    $payload = '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /ImagePullBackOff/ | sort @timestamp desc","limit":10}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload $payload image_pull_logs.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 5: Testing remediation..." -ForegroundColor Yellow
    $remediationPayload = '{"operation":"rollout_restart","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"image-pull-test","dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload $remediationPayload image_pull_fix.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 6: Cleaning up..." -ForegroundColor Yellow
    kubectl delete deployment image-pull-test
    Remove-Item -Path "image_pull_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ ImagePullBackOff scenario completed" -ForegroundColor Green
}

# Readiness Probe Scenario
function Run-ReadinessScenario {
    Write-Host "`n📋 Readiness Probe Failure Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Deploying with failing readiness probe"
    Write-Host "2. Detecting readiness probe failures"
    Write-Host "3. Applying remediation"
    
    Write-Host "`nStep 1: Deploying with failing readiness probe..." -ForegroundColor Yellow
    
    $deploymentYaml = @"
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
"@
    
    $deploymentYaml | kubectl apply -f -
    
    Write-Host "`nStep 2: Waiting for readiness probe failures..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host "`nStep 3: Checking pod status..." -ForegroundColor Yellow
    kubectl get pods -l app=readiness-test
    
    Write-Host "`nStep 4: Testing detection..." -ForegroundColor Yellow
    $payload = '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /Readiness probe failed/ | sort @timestamp desc","limit":10}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload $payload readiness_logs.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 5: Testing remediation..." -ForegroundColor Yellow
    $remediationPayload = '{"operation":"patch_deployment","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"readiness-test","patch":{"spec":{"template":{"spec":{"containers":[{"name":"nginx","readinessProbe":{"httpGet":{"path":"/","port":80},"initialDelaySeconds":5,"periodSeconds":5}}]}}}},"dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload $remediationPayload readiness_fix.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 6: Cleaning up..." -ForegroundColor Yellow
    kubectl delete deployment readiness-test
    Remove-Item -Path "readiness_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ Readiness probe scenario completed" -ForegroundColor Green
}

# CrashLoopBackOff Scenario
function Run-CrashLoopScenario {
    Write-Host "`n📋 CrashLoopBackOff Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Deploying with crashing container"
    Write-Host "2. Detecting CrashLoopBackOff"
    Write-Host "3. Applying remediation"
    
    Write-Host "`nStep 1: Deploying crashing application..." -ForegroundColor Yellow
    
    $deploymentYaml = @"
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
"@
    
    $deploymentYaml | kubectl apply -f -
    
    Write-Host "`nStep 2: Waiting for CrashLoopBackOff..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Write-Host "`nStep 3: Checking pod status..." -ForegroundColor Yellow
    kubectl get pods -l app=crash-test
    
    Write-Host "`nStep 4: Testing detection..." -ForegroundColor Yellow
    $payload = '{"log_groups":["/aws/eks/eks-chaos-guardian-autopilot/application"],"query":"fields @timestamp, @message | filter @message like /CrashLoopBackOff/ | sort @timestamp desc","limit":10}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-logs --payload $payload crash_logs.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 5: Testing remediation..." -ForegroundColor Yellow
    $remediationPayload = '{"operation":"rollout_restart","cluster":"eks-chaos-guardian-autopilot","namespace":"default","resource_name":"crash-test","dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-k8s-operations --payload $remediationPayload crash_fix.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 6: Cleaning up..." -ForegroundColor Yellow
    kubectl delete deployment crash-test
    Remove-Item -Path "crash_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ CrashLoopBackOff scenario completed" -ForegroundColor Green
}

# Network Latency Scenario
function Run-NetworkScenario {
    Write-Host "`n📋 Network Latency Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Injecting network latency"
    Write-Host "2. Detecting performance issues"
    Write-Host "3. Applying remediation"
    
    Write-Host "`nStep 1: Testing network latency injection (dry run)..." -ForegroundColor Yellow
    $payload = '{"cluster":"eks-chaos-guardian-autopilot","latency_ms":100,"duration_seconds":60,"dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-network-latency --payload $payload network_latency.json --profile eks-chaos-guardian
    
    if (Test-Path "network_latency.json") {
        Write-Host "✅ Network latency injection planned" -ForegroundColor Green
        Get-Content network_latency.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    
    Write-Host "`nStep 2: Testing metrics detection..." -ForegroundColor Yellow
    $metricsPayload = '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload $metricsPayload network_metrics.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 3: Cleaning up..." -ForegroundColor Yellow
    Remove-Item -Path "network_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ Network latency scenario completed" -ForegroundColor Green
}

# API Throttling Scenario
function Run-APIThrottleScenario {
    Write-Host "`n📋 API Throttling Scenario" -ForegroundColor Blue
    Write-Host "This scenario demonstrates:"
    Write-Host "1. Injecting API throttling"
    Write-Host "2. Detecting throttling effects"
    Write-Host "3. Applying remediation"
    
    Write-Host "`nStep 1: Testing API throttling injection (dry run)..." -ForegroundColor Yellow
    $payload = '{"cluster":"eks-chaos-guardian-autopilot","throttle_rate":0.5,"duration_seconds":60,"dry_run":true}'
    aws lambda invoke --function-name eks-chaos-guardian-api-throttling --payload $payload api_throttle.json --profile eks-chaos-guardian
    
    if (Test-Path "api_throttle.json") {
        Write-Host "✅ API throttling injection planned" -ForegroundColor Green
        Get-Content api_throttle.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
    }
    
    Write-Host "`nStep 2: Testing metrics detection..." -ForegroundColor Yellow
    $metricsPayload = '{"namespace":"AWS/EKS","dimensions":{"ClusterName":"eks-chaos-guardian-autopilot"},"period":300}'
    aws lambda invoke --function-name eks-chaos-guardian-cloudwatch-metrics --payload $metricsPayload api_metrics.json --profile eks-chaos-guardian
    
    Write-Host "`nStep 3: Cleaning up..." -ForegroundColor Yellow
    Remove-Item -Path "api_*.json" -ErrorAction SilentlyContinue
    
    Write-Host "✅ API throttling scenario completed" -ForegroundColor Green
}

# Run All Scenarios
function Run-AllScenarios {
    Write-Host "`n🎬 Running All Demo Scenarios" -ForegroundColor Magenta
    Write-Host "==================================" -ForegroundColor Magenta
    
    Run-OOMKilledScenario
    Run-ImagePullScenario
    Run-ReadinessScenario
    Run-CrashLoopScenario
    Run-NetworkScenario
    Run-APIThrottleScenario
    
    Write-Host "`n🎉 All demo scenarios completed!" -ForegroundColor Green
}

# Main execution
if (-not $Scenario) {
    Show-Usage
    exit 1
}

# Run the specified scenario
Run-Scenario $Scenario
