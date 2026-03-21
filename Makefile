# CoKeeper Deployment Makefile
# Combines Terraform and gcloud for flexible deployment

.PHONY: help init plan apply deploy-dev deploy-prod test-local clean destroy

PROJECT_ID := co-keeper-run-1773629710
REGION := us-central1

help: ## Show this help message
	@echo "CoKeeper Deployment Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Local Development ---

test-local: ## Run local backend and frontend for testing
	@echo "Starting local testing environment..."
	./test_local.sh

install: ## Install Python dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && pip install -r requirements.txt

# --- Quick Deploy (gcloud) ---

deploy-dev: ## Quick deploy both services (development)
	@echo "🚀 Quick deploying to Cloud Run (dev mode)..."
	./deploy-simple.sh

deploy-backend: ## Deploy only backend
	@echo "🚀 Deploying backend..."
	gcloud run deploy cokeeper-backend \
		--source ./backend \
		--region $(REGION) \
		--allow-unauthenticated \
		--port 8000 \
		--memory 2Gi \
		--cpu 2 \
		--timeout 300 \
		--project $(PROJECT_ID)

deploy-frontend: ## Deploy only frontend
	@echo "🚀 Deploying frontend..."
	@BACKEND_URL=$$(gcloud run services describe cokeeper-backend --region=$(REGION) --format='value(status.url)' --project=$(PROJECT_ID)); \
	gcloud run deploy cokeeper-frontend \
		--source ./frontend \
		--region $(REGION) \
		--allow-unauthenticated \
		--port 8501 \
		--memory 1Gi \
		--cpu 1 \
		--timeout 300 \
		--set-env-vars BACKEND_URL=$$BACKEND_URL \
		--project $(PROJECT_ID)

# --- Terraform (IaC) ---

init: ## Initialize Terraform
	cd terraform && terraform init

plan: ## Preview Terraform changes
	cd terraform && terraform plan

apply: ## Apply Terraform configuration
	cd terraform && terraform apply

deploy-prod: apply ## Deploy with Terraform (production)
	@echo "✅ Production deployment complete"
	@cd terraform && terraform output

# --- Utilities ---

logs-backend: ## Tail backend logs
	gcloud run services logs tail cokeeper-backend --region=$(REGION) --project=$(PROJECT_ID)

logs-frontend: ## Tail frontend logs
	gcloud run services logs tail cokeeper-frontend --region=$(REGION) --project=$(PROJECT_ID)

status: ## Show service status
	@echo "Backend:"
	@gcloud run services describe cokeeper-backend --region=$(REGION) --format='value(status.url)' --project=$(PROJECT_ID)
	@echo ""
	@echo "Frontend:"
	@gcloud run services describe cokeeper-frontend --region=$(REGION) --format='value(status.url)' --project=$(PROJECT_ID)

clean: ## Clean up local artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf models/*.pkl 2>/dev/null || true

destroy: ## Destroy all Cloud Run services (Terraform)
	cd terraform && terraform destroy

# --- Import existing resources to Terraform ---

import: ## Import existing Cloud Run services to Terraform
	cd terraform && \
	terraform import google_cloud_run_v2_service.backend projects/$(PROJECT_ID)/locations/$(REGION)/services/cokeeper-backend || true && \
	terraform import google_cloud_run_v2_service.frontend projects/$(PROJECT_ID)/locations/$(REGION)/services/cokeeper-frontend || true
	@echo "✅ Resources imported. Run 'make plan' to see state"
