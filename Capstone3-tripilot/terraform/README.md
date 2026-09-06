# Terraform → GCP Cloud Run (cloud deployment bonus)

Cloud Run is used instead of serverless static hosting because it runs the
**long-lived Streamlit container** itself over HTTPS.

## Steps

```bash
# 0) one-time auth
gcloud auth application-default login
export TF_VAR_gcp_project_id=<your-gcp-project-id>

# 1) provision APIs + artifact registry
terraform init
terraform apply -target=google_artifact_registry_repository.tripilot

# 2) build + push the image
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/$TF_VAR_gcp_project_id/tripilot/tripilot-app:latest .
docker push us-central1-docker.pkg.dev/$TF_VAR_gcp_project_id/tripilot/tripilot-app:latest

# 3) deploy the public service
terraform apply
terraform output cloud_run_service_url   # <- paste this live URL into README.md
```

> Note: the Cloud Run deployment is stateless; telemetry falls back to
> SQLite inside the container. For the full Postgres+Grafana stack keep
> using `docker compose` / Kubernetes locally. Destroy with
> `terraform destroy` to stay inside the free tier.
