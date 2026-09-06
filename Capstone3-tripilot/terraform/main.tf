terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.region
}

# --- APIs ----------------------------------------------------------------
resource "google_project_service" "run" {
  service = "run.googleapis.com"
}
resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
}
resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
}

# --- Artifact Registry for the container image ---------------------------
resource "google_artifact_registry_repository" "tripilot" {
  location      = var.region
  repository_id = "tripilot"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifactregistry]
}

# --- Cloud Run v2 service hosting the Streamlit app ----------------------
resource "google_cloud_run_v2_service" "tripilot" {
  name     = "tripilot-app"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.gcp_project_id}/tripilot/tripilot-app:latest"
      ports {
        container_port = 8501
      }
      env {
        name  = "GROQ_API_KEY"
        value = var.groq_api_key
      }
      env {
        name  = "LLM_PROVIDER"
        value = "groq"
      }
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }
  depends_on = [google_project_service.run]
}

# --- Public HTTPS access ---------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.gcp_project_id
  location = var.region
  name     = google_cloud_run_v2_service.tripilot.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
