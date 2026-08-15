variable "gcp_project_id" {
  type        = string
  description = "GCP project id, e.g. llm-zoomcamp-capstone. Find it at https://console.cloud.google.com (or: gcloud config get-value project)."
}

variable "gcp_region" {
  type        = string
  default     = "us-central1"
  description = "GCP region for Cloud Run and Artifact Registry."
}

variable "service_name" {
  type        = string
  default     = "complaintradar"
  description = "Cloud Run service name (also the URL slug)."
}

variable "artifact_repo" {
  type        = string
  default     = "complaintradar"
  description = "Artifact Registry Docker repository name."
}

variable "container_image" {
  type        = string
  default     = ""
  description = "Full container image path. Leave empty to use <region>-docker.pkg.dev/<project>/<artifact_repo>/complaintradar-app:latest."
}

variable "container_port" {
  type        = number
  default     = 8501
  description = "Port the Streamlit app listens on inside the container (matches the Dockerfile)."
}

variable "cpu" {
  type        = string
  default     = "1"
  description = "CPU per instance (e.g. \"1\", \"2\")."
}

variable "memory" {
  type        = string
  default     = "2Gi"
  description = "Memory per instance (e.g. \"1Gi\", \"2Gi\", \"4Gi\")."
}

variable "min_instances" {
  type        = number
  default     = 0
  description = "Minimum instances. 0 = scale to zero; the first request after a deploy cold-starts in ~1-2 minutes."
}

variable "max_instances" {
  type        = number
  default     = 1
  description = "Maximum instances. 1 keeps the app's SQLite/index-cache fallback state consistent for the demo."
}

variable "max_concurrency" {
  type        = number
  default     = 5
  description = "Max concurrent requests per instance (Streamlit sessions are long-lived)."
}

variable "groq_api_key" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Optional Groq API key, injected as GROQ_API_KEY. Without it the app runs in built-in mock mode."
}

variable "credentials_file" {
  type        = string
  default     = ""
  description = "Optional path to a GCP service-account JSON key. Leave empty to use gcloud Application Default Credentials."
}
