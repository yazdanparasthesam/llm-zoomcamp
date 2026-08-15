output "cloud_run_service_url" {
  value       = google_cloud_run_v2_service.complaintradar.uri
  description = "Public HTTPS URL of the live Streamlit app. Paste this into the README 'Live Streamlit app' line for the +2 cloud rubric."
}

output "cloud_run_service_name" {
  value       = google_cloud_run_v2_service.complaintradar.name
  description = "Cloud Run service name."
}

output "cloud_run_console" {
  value       = "https://console.cloud.google.com/run/detail/${var.gcp_region}/${var.service_name}/metrics?project=${var.gcp_project_id}"
  description = "Link to the service in the Google Cloud console."
}

output "artifact_registry_image" {
  value       = local.container_image
  description = "Container image the service runs. Build and push it before terraform apply (see terraform/README.md)."
}

output "live_url_note" {
  value       = "First request after a deploy cold-starts (~1-2 min with min_instances=0). With no GROQ_API_KEY set the app answers in built-in mock mode."
  description = "Operational notes for reviewers."
}
