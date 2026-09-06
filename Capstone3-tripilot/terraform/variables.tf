variable "gcp_project_id" {
  description = "GCP project id that will host the Cloud Run service"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run + Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "groq_api_key" {
  description = "Groq API key injected into the app container (leave empty for offline mock mode)"
  type        = string
  default     = ""
  sensitive   = true
}
