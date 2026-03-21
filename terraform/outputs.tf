output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "backend_service_name" {
  description = "Name of the backend service"
  value       = google_cloud_run_v2_service.backend.name
}

output "frontend_service_name" {
  description = "Name of the frontend service"
  value       = google_cloud_run_v2_service.frontend.name
}
