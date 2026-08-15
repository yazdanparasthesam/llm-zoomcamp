# ---------------------------------------------------------------------------
# ComplaintRadar — Google Cloud Platform (GCP) deployment via Terraform.
#
# What this creates (fully serverless — no VMs):
#   1. Required GCP APIs (Cloud Run, Artifact Registry, Cloud Build, IAM).
#   2. An Artifact Registry Docker repository to hold the app image.
#   3. A public Cloud Run v2 service running the Dockerized Streamlit RAG app
#      over HTTPS — this is the live URL the capstone rubric requires.
#   4. An IAM binding granting allUsers the Cloud Run invoker role so the
#      service opens in a browser without authentication.
#
# Why Cloud Run instead of Vercel: Vercel is static/serverless-only and can
# NOT run `streamlit run` + Postgres + Grafana. Cloud Run runs the long-lived
# Streamlit container. The app ships a zero-config fallback (SQLite +
# data/index_cache.json), so it works here without Elasticsearch/Postgres;
# set GROQ_API_KEY for real LLM answers (see terraform/README.md).
#
# Image build & push happens OUTSIDE Terraform (see terraform/README.md):
#   gcloud builds submit --tag <artifact_registry_image> .
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  # Credentials come from gcloud Application Default Credentials
  # (`gcloud auth application-default login`) or from var.credentials_file.
  credentials = var.credentials_file == "" ? null : file(var.credentials_file)
}

# --- 1. Enable required GCP APIs --------------------------------------------
resource "google_project_service" "cloud_run" {
  project            = var.gcp_project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  project            = var.gcp_project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build" {
  project            = var.gcp_project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  project            = var.gcp_project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

# --- 2. Artifact Registry Docker repository ---------------------------------
resource "google_artifact_registry_repository" "complaintradar" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = var.artifact_repo
  description   = "Docker images for the ComplaintRadar Streamlit RAG app"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Default image tag the Cloud Run service runs (override via var.container_image)
locals {
  container_image = var.container_image == "" ? (
    "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${var.artifact_repo}/complaintradar-app:latest"
  ) : var.container_image

  # The env block's for_each cannot consume a sensitive value; the boolean
  # itself reveals nothing about the key (the key value stays redacted).
  set_groq_env = nonsensitive(var.groq_api_key != "")
}

# --- 3. Cloud Run v2 service (public) ----------------------------------------
resource "google_cloud_run_v2_service" "complaintradar" {
  name                = var.service_name
  project             = var.gcp_project_id
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    # Streamlit sessions are long-lived WebSocket connections, so keep the
    # per-instance concurrency modest.
    max_instance_request_concurrency = var.max_concurrency

    containers {
      image = local.container_image

      ports {
        name           = "http1"
        container_port = var.container_port
      }

      # Only injected when a key is provided; without it the app runs in
      # built-in mock mode (still fully browsable).
      dynamic "env" {
        for_each = local.set_groq_env ? toset(["set"]) : toset([])
        content {
          name  = "GROQ_API_KEY"
          value = var.groq_api_key
        }
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Give Streamlit time to boot on cold starts before traffic is routed.
      # (Cloud Run pins the startup-probe failure threshold to 1, so the
      # long period_seconds/timeout_seconds is what provides the grace time.)
      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 240
        period_seconds        = 240
        failure_threshold     = 1
        tcp_socket {
          port = var.container_port
        }
      }

      liveness_probe {
        timeout_seconds   = 5
        period_seconds    = 30
        failure_threshold = 3
        http_get {
          path = "/_stcore/health"
          port = var.container_port
        }
      }
    }

    scaling {
      # 0 = scale to zero (first request cold-starts in ~1–2 min).
      # 1 = always warm, but billed 24/7.
      min_instance_count = var.min_instances
      # Single instance keeps the app's SQLite / index-cache fallback state
      # consistent for the demo (no shared DB inside Cloud Run).
      max_instance_count = var.max_instances
    }
  }

  depends_on = [google_project_service.cloud_run]
}

# --- 4. Public access: allUsers can invoke the service ------------------------
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.complaintradar.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
