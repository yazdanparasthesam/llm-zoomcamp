variable "project_id" {
  description = "Google Cloud Project ID for deployment"
  type        = string
  default     = "findocs-copilot-cloud"
}

variable "region" {
  description = "GCP deployment region"
  type        = string
  default     = "us-central1"
}
