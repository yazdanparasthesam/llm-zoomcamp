output "cloud_run_service_url" {
  description = "Live public URL of the TripPilot Streamlit app (paste into README)"
  value       = google_cloud_run_v2_service.tripilot.uri
}

output "artifact_registry_repo" {
  description = "Docker repo to push the app image to"
  value       = google_artifact_registry_repository.tripilot.id
}
