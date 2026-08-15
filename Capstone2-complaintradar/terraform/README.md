# Terraform → GCP Cloud Run (ComplaintRadar)

## What Terraform creates
1. **Enabled GCP APIs** — Cloud Run, Artifact Registry, Cloud Build, IAM.
2. **Artifact Registry Docker repository** (`complaintradar`) to hold the app image.
3. **Cloud Run v2 service** (`complaintradar`) running the Dockerized **Streamlit RAG app** behind a **public HTTPS URL**.
4. **Public IAM binding** — `allUsers` get `roles/run.invoker`, so the app opens in a browser with no authentication.

## Why Cloud Run (and not Vercel)
Vercel is serverless-static only and **cannot** run `streamlit run` + Postgres + Grafana. **Cloud Run runs the long-lived Streamlit container**, so the URL Terraform produces is the **live interactive app** reviewers click for the +2 cloud rubric. The app ships a zero-config fallback (SQLite + `data/index_cache.json`), so it works on Cloud Run without Elasticsearch/Postgres; provide `GROQ_API_KEY` for real LLM answers.

## Prerequisites
- A GCP project with **billing enabled**: https://console.cloud.google.com
- **gcloud CLI** installed and authenticated (`gcloud auth login`)
- **Terraform ≥ 1.5**
- For image push: local Docker, or use **Cloud Build** (no local Docker needed)

## Deploy

### 1. Authenticate Terraform
```bash
gcloud auth application-default login
```
(Alternative: `export TF_VAR_credentials_file=/path/to/service-account-key.json`)

### 2. Build & push the app image (from the repository root)
```bash
export GCP_PROJECT_ID="your-project-id"   # e.g. llm-zoomcamp-capstone
export GCP_REGION="us-central1"

# Option A: Cloud Build (no local Docker needed)
gcloud builds submit \
  --region "$GCP_REGION" \
  --tag "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/complaintradar/complaintradar-app:latest" .

# Option B: local Docker
# docker build -t "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/complaintradar/complaintradar-app:latest" .
# docker push "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/complaintradar/complaintradar-app:latest"
```

### 3. Provision with Terraform
```bash
cd terraform
export TF_VAR_gcp_project_id="$GCP_PROJECT_ID"
export TF_VAR_gcp_region="$GCP_REGION"
# optional (otherwise the app runs in mock mode):
# export TF_VAR_groq_api_key="$GROQ_API_KEY"

terraform init
terraform plan
terraform apply
```

### 4. Grab the live URL
```bash
terraform output cloud_run_service_url
# e.g. https://complaintradar-xxxxxxxxxx-uc.a.run.app
```
Paste it into the main `README.md` "Live Streamlit app" line (Step 10 / Option C) — that is the URL reviewers click.

> **Cold-start note:** with `min_instances = 0` the first request after a deploy can take **~1–2 minutes**. If you want instant loads during the demo, set `export TF_VAR_min_instances=1` (billed 24/7, roughly $15–20/month for 1 vCPU / 2 GiB).

## Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `gcp_project_id` | — (required) | GCP project id, e.g. `llm-zoomcamp-capstone` |
| `gcp_region` | `us-central1` | Region for Cloud Run + Artifact Registry |
| `service_name` | `complaintradar` | Cloud Run service name / URL slug |
| `artifact_repo` | `complaintradar` | Artifact Registry Docker repo name |
| `container_image` | *(computed)* | Image path; empty = `<region>-docker.pkg.dev/<project>/<repo>/complaintradar-app:latest` |
| `container_port` | `8501` | Streamlit port inside the container (must match the Dockerfile) |
| `cpu` / `memory` | `1` / `2Gi` | Resources per instance |
| `min_instances` | `0` | Scale to zero (cold start ~1–2 min) or `1` = always warm |
| `max_instances` | `1` | 1 keeps the SQLite/index-cache fallback state consistent for the demo |
| `max_concurrency` | `5` | Concurrent requests per instance (Streamlit sessions are long-lived) |
| `groq_api_key` | `""` | Optional `GROQ_API_KEY` env var injected into the service |
| `credentials_file` | `""` | Optional SA JSON key; empty = gcloud ADC |

## Static landing page
The static landing (`public/index.html`) is **not** part of this Terraform — serve it from any static host (GitHub Pages, Netlify, or a GCS bucket) if needed. Cloud Run already hosts the interactive app itself.

## Teardown
```bash
terraform destroy
```
Also delete the pushed image (or the whole repo) in Artifact Registry to stop storage charges.
