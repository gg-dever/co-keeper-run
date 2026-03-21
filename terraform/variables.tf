variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "co-keeper-run-1773629710"
}

variable "region" {
  description = "GCP region for Cloud Run services"
  type        = string
  default     = "us-central1"
}

variable "backend_image" {
  description = "Docker image for backend (use 'gcr.io/PROJECT_ID/SERVICE:latest' or source deployment)"
  type        = string
  default     = "gcr.io/co-keeper-run-1773629710/cokeeper-backend:latest"
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
  default     = "gcr.io/co-keeper-run-1773629710/cokeeper-frontend:latest"
}
