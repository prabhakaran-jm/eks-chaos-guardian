# EKS Chaos Guardian - Build and Deploy Scripts

.PHONY: help deploy destroy demo-oom demo-image-pull demo-readiness demo-disk demo-pdb demo-coredns clean ui-start ui-stop

help: ## Show this help message
	@echo "EKS Chaos Guardian - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

deploy: ## Deploy the complete infrastructure
	@echo "🚀 Deploying EKS Chaos Guardian infrastructure..."
	cd infra && terraform init
	cd infra && terraform plan -out=tfplan
	cd infra && terraform apply tfplan
	@echo "✅ Infrastructure deployed successfully!"

destroy: ## Destroy all infrastructure
	@echo "🗑️ Destroying infrastructure..."
	cd infra && terraform destroy -auto-approve
	@echo "✅ Infrastructure destroyed"

demo-oom: ## Run OOMKilled scenario demo
	@echo "🧪 Running OOMKilled scenario..."
	python demo/scenarios/oomkilled.py

demo-image-pull: ## Run ImagePullBackOff scenario demo
	@echo "🧪 Running ImagePullBackOff scenario..."
	python demo/scenarios/image_pull_backoff.py

demo-readiness: ## Run Readiness Probe scenario demo
	@echo "🧪 Running Readiness Probe scenario..."
	python demo/scenarios/readiness_probe.py

demo-disk: ## Run Disk Pressure scenario demo
	@echo "🧪 Running Disk Pressure scenario..."
	python demo/scenarios/disk_pressure.py

demo-pdb: ## Run PDB Blocking scenario demo
	@echo "🧪 Running PDB Blocking scenario..."
	python demo/scenarios/pdb_blocking.py

demo-coredns: ## Run CoreDNS Failure scenario demo
	@echo "🧪 Running CoreDNS Failure scenario..."
	python demo/scenarios/coredns_failure.py

demo-all: ## Run all demo scenarios
	@echo "🧪 Running all demo scenarios..."
	$(MAKE) demo-oom
	$(MAKE) demo-image-pull
	$(MAKE) demo-readiness
	$(MAKE) demo-disk
	$(MAKE) demo-pdb
	$(MAKE) demo-coredns

ui-start: ## Start the web UI dashboard
	@echo "🌐 Starting EKS Chaos Guardian Web UI..."
	cd ui && python server.py

ui-stop: ## Stop the web UI dashboard
	@echo "🛑 Stopping Web UI..."
	pkill -f "python server.py" || true

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	rm -rf infra/.terraform
	rm -rf infra/terraform.tfstate*
	rm -rf infra/tfplan
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

setup-dev: ## Setup development environment
	@echo "🛠️ Setting up development environment..."
	pip install -r requirements.txt
	pre-commit install
	@echo "✅ Development environment ready!"

test: ## Run tests
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

lint: ## Run linting
	@echo "🔍 Running linting..."
	flake8 lambda/ demo/ tests/
	black --check lambda/ demo/ tests/

format: ## Format code
	@echo "🎨 Formatting code..."
	black lambda/ demo/ tests/
	isort lambda/ demo/ tests/

# Infrastructure status
status: ## Show infrastructure status
	@echo "📊 Infrastructure Status:"
	cd infra && terraform show -json | jq '.values.root_module.resources[] | select(.type | startswith("aws_")) | {type: .type, name: .name, status: "active"}'

# Get API Gateway URL
api-url: ## Get API Gateway URL
	@echo "🌐 API Gateway URL:"
	cd infra && terraform output -raw api_gateway_url

# Get Slack webhook URL (for setup)
slack-webhook: ## Get Slack webhook URL setup instructions
	@echo "📱 Slack Webhook Setup:"
	@echo "1. Go to your Slack workspace"
	@echo "2. Create a new app at https://api.slack.com/apps"
	@echo "3. Enable Incoming Webhooks"
	@echo "4. Copy the webhook URL"
	@echo "5. Set it in your environment: export SLACK_WEBHOOK_URL=<your-webhook-url>"
