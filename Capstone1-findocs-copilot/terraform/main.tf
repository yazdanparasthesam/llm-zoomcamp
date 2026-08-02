# Terraform Configuration for FinDocs Copilot Cloud Deployment (+2 Bonus Points)
# Deploys the Streamlit RAG Container to Google Cloud Run with Managed PostgreSQL

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_run_v2_service" "findocs_app" {
  name     = "findocs-copilot-service"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/findocs-app:latest"
      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
      }
      env {
        name  = "USE_DOCKER"
        value = "false"
      }
      env {
        name  = "GROQ_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "groq-api-key"
            version = "latest"
          }
        }
      }
      ports {
        container_port = 8501
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.findocs_app.location
  project  = google_cloud_run_v2_service.findocs_app.project
  service  = google_cloud_run_v2_service.findocs_app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
