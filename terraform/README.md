# CoKeeper Terraform Configuration

Infrastructure as Code for CoKeeper Cloud Run deployment.

## Quick Start

### Option 1: Terraform (Full IaC Management)
**Use when:** Production deployments, team collaboration, tracking infrastructure changes

```bash
cd terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply

# Get service URLs
terraform output
```

### Option 2: Quick Deploy Scripts (Fast Iteration)
**Use when:** Development, testing fixes, rapid iteration

```bash
# From repo root
./deploy-simple.sh

# Or deploy individually
gcloud run deploy cokeeper-backend --source ./backend --region us-central1 --allow-unauthenticated
gcloud run deploy cokeeper-frontend --source ./frontend --region us-central1 --allow-unauthenticated
```

## Hybrid Workflow

**Best of both worlds:**

1. **Initial Setup & Production:** Use Terraform
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. **Development Iterations:** Use gcloud directly
   ```bash
   ./deploy-simple.sh  # Much faster for testing
   ```

3. **Sync Changes:** Import manual changes back to Terraform
   ```bash
   terraform refresh  # Update state with manual changes
   terraform plan     # See drift
   ```

4. **Production Release:** Use Terraform for final deployment
   ```bash
   terraform apply
   ```

## Configuration

Edit `variables.tf` or create `terraform.tfvars`:

```hcl
project_id = "co-keeper-run-1773629710"
region     = "us-central1"
```

## State Management

**Local State (Default):**
- State stored in `terraform.tfstate`
- Fine for single-developer testing
- Commit to Git with caution

**Remote State (Recommended):**
Uncomment backend in `main.tf` after creating bucket:

```bash
gsutil mb gs://co-keeper-terraform-state
echo "Delete after 30 days" | gsutil lifecycle set /dev/stdin gs://co-keeper-terraform-state
```

Then uncomment in `main.tf`:
```hcl
backend "gcs" {
  bucket = "co-keeper-terraform-state"
  prefix = "prod"
}
```

## Commands

```bash
# Initialize
terraform init

# Format code
terraform fmt

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Import existing resource
terraform import google_cloud_run_v2_service.backend projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME
```

## Troubleshooting

**"Resource already exists":**
```bash
# Import existing resources
terraform import google_cloud_run_v2_service.backend projects/co-keeper-run-1773629710/locations/us-central1/services/cokeeper-backend
terraform import google_cloud_run_v2_service.frontend projects/co-keeper-run-1773629710/locations/us-central1/services/cokeeper-frontend
```

**State out of sync:**
```bash
terraform refresh
terraform plan  # Review differences
```

**Start fresh:**
```bash
rm -rf .terraform terraform.tfstate*
terraform init
terraform import ...  # Import existing resources
```
