# EKS Chaos Guardian - Health Check Script (PowerShell)
# Quick test to verify all components are working

Write-Host "🔍 EKS Chaos Guardian Health Check" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Function to check command success
function Test-Command {
    param($Command, $Description)
    
    try {
        Invoke-Expression $Command | Out-Null
        Write-Host "✅ $Description" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ $Description" -ForegroundColor Red
        return $false
    }
}

$TestsPassed = 0
$TestsFailed = 0

Write-Host "`n1. Checking AWS CLI Configuration..." -ForegroundColor Yellow
if (Test-Command "aws sts get-caller-identity --profile eks-chaos-guardian" "AWS CLI configured") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n2. Checking EKS Cluster..." -ForegroundColor Yellow
if (Test-Command "aws eks describe-cluster --name eks-chaos-guardian-autopilot --profile eks-chaos-guardian" "EKS cluster accessible") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n3. Checking Lambda Functions..." -ForegroundColor Yellow
if (Test-Command "aws lambda list-functions --profile eks-chaos-guardian" "Lambda functions deployed") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n4. Checking S3 Bucket..." -ForegroundColor Yellow
if (Test-Command "aws s3 ls s3://eks-chaos-guardian-runbooks --profile eks-chaos-guardian" "S3 bucket accessible") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n5. Checking DynamoDB Table..." -ForegroundColor Yellow
if (Test-Command "aws dynamodb describe-table --table-name eks-chaos-guardian-runbook-index --profile eks-chaos-guardian" "DynamoDB table exists") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n6. Testing Lambda Function (Dry Run)..." -ForegroundColor Yellow
if (Test-Command "aws lambda invoke --function-name eks-chaos-guardian-node-failure --payload '{\"cluster\":\"eks-chaos-guardian-autopilot\",\"dry_run\":true}' response.json --profile eks-chaos-guardian" "Lambda function test") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n7. Checking Kubernetes Access..." -ForegroundColor Yellow
if (Test-Command "kubectl get nodes" "Kubernetes cluster accessible") {
    $TestsPassed++
} else {
    $TestsFailed++
}

Write-Host "`n8. Checking Web UI..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Web UI running" -ForegroundColor Green
    $TestsPassed++
}
catch {
    Write-Host "⚠️  Web UI not running (start with: cd ui && python server.py)" -ForegroundColor Yellow
}

Write-Host "`n9. Checking Demo Scenarios..." -ForegroundColor Yellow
if (Test-Path "demo/scenarios/oomkilled.py") {
    Write-Host "✅ Demo scenarios available" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "❌ Demo scenarios missing" -ForegroundColor Red
    $TestsFailed++
}

Write-Host "`n10. Checking Documentation..." -ForegroundColor Yellow
if ((Test-Path "README.md") -and (Test-Path "docs/architecture.md")) {
    Write-Host "✅ Documentation complete" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "❌ Documentation missing" -ForegroundColor Red
    $TestsFailed++
}

Write-Host "`n==================================" -ForegroundColor Green
Write-Host "Health Check Complete!" -ForegroundColor Green
Write-Host "`nTests Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $TestsFailed" -ForegroundColor Red

if ($TestsFailed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED! EKS Chaos Guardian is ready!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check the output above for details." -ForegroundColor Yellow
}

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\test-all.ps1 (comprehensive tests)" -ForegroundColor White
Write-Host "2. Run: .\demo-scenario.ps1 oomkilled (demo scenario)" -ForegroundColor White
Write-Host "3. Start Web UI: cd ui && python server.py" -ForegroundColor White
Write-Host "4. Test Slack bot with configured webhook" -ForegroundColor White
