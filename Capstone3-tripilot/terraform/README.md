# Azure deployment with Terraform

This directory now contains an **Azure Terraform implementation** of the hosting architecture described in Step 11 of the [main README](../README.md). It deploys Azure Container Apps and Azure Container Registry, with Groq as the optional model provider. **The Google provider and GCP resources have been removed from these `.tf` files.**

The [Azure CLI/Bicep walkthrough](../azure/README-azure.md) remains an alternative implementation. Choose **Terraform or CLI/Bicep** for a deployment; do not manage the same resources with both. The Terraform default group is `rg-tripilot-capstone3-tf`, separate from the CLI/Bicep example.

**Migration warning:** do not apply this configuration against an existing GCP Terraform state or backend. Preserve any old state and manage its resources with the original GCP configuration. Do not delete state to hide existing resources. Use a fresh, private state for this Azure deployment. Existing Azure resources also require a deliberate import/ownership plan rather than a blind first apply.

## What Terraform manages

| Component | Configuration |
|---|---|
| Provider | `hashicorp/azurerm` **4.81.0**; Terraform **1.9 or newer, below 2.0** |
| Subscription checks | Require **Enabled**, **spending limit On**, and explicit credit-offer confirmation |
| Resource group | Dedicated Terraform-owned group with project tags |
| Container Registry | Standard SKU, admin account disabled, ARM-audience authentication enabled |
| Image access | User-assigned managed identity; `AcrPull` scoped to this registry only |
| Environment | Consumption-only, without a Log Analytics workspace or dedicated workload profile |
| App | Streamlit container, **0.5 vCPU / 1 GiB**, zero to one replica, single active revision |
| Ingress | Public HTTPS to port **8501**; insecure HTTP disabled |
| Health probes | HTTP startup, readiness, and liveness probes on `/healthz` |
| Image version | An immutable digest from this deployment's own registry |
| Default model mode | No-key offline mock; no Groq secret is required |
| Optional live mode | Groq key stored as a Container Apps secret and referenced by the environment |
| Telemetry | Ephemeral SQLite and JSONL inside the container |

No Azure OpenAI resource, cloud PostgreSQL, Elasticsearch, Grafana, Key Vault, or paid Marketplace product is created by this module. Container-local records can reset on restarts, replacement, revisions, or scale-to-zero. The existing local Compose/Kind evidence remains separate.

## Budget and credentials

Use only an eligible Azure credit offer under the selected project constraints. Confirm available credit and expiry in the portal before each apply. The subscription data source checks **Enabled + spending limit On**, but it does not know the remaining credit balance or expiry. A Standard registry may be covered by an eligible free-service allowance; otherwise it consumes credits at the applicable rate. Scale-to-zero does not stop registry charges.

Do not remove the spending limit, upgrade to Pay-As-You-Go, or purchase a paid Groq plan to bypass a failed check. Azure credits do not cover Groq invoices or every external Marketplace charge.

**Terraform secret warning:** `sensitive = true` hides a key in ordinary CLI output, but it does **not** keep it out of Terraform state or saved plans. Live mode puts the Groq key in those files. Keep state and plans in a protected location outside Git and outside the Docker build context, and use encrypted, access-controlled storage if sharing state. Never publish state, plans, `.tfvars` containing credentials, or debug logs. The no-key default avoids storing a model key.

## Prerequisites

- Azure CLI authenticated to the intended credit subscription.
- Terraform 1.9+ and Docker.
- Permission to create the dedicated resources and assign the registry-scoped role.
- The current TripPilot source and pinned Python dependencies in the Dockerfile.

Provider registration is deliberately not automatic: `resource_provider_registrations = "none"`. Register the required providers only after the credit checks below.

## 1. Prepare a private configuration

Run commands individually from the **project root containing `app.py`**, not from the course-repository root. Stop on any error and review each plan before its apply; do not continue with stale output from a failed command. Use `~/Documents/tripilot` for the standalone working copy, or enter your clone's `Capstone3-tripilot` folder.

```bash
cd ~/Documents/tripilot                    # change this to your actual TripPilot project root if needed
test -f app.py && test -f terraform/main.tf # confirm the build context and Terraform directory
umask 077                                 # create private local files with owner-only access
az login --output none                    # authenticate using your own Azure account
az account list --query '[].{Name:name,ID:id,State:state}' --output table  # find the intended credit subscription
read -r -p 'Azure subscription UUID: ' SUBSCRIPTION_ID  # enter the subscription ID, not an API key
az account set --subscription "$SUBSCRIPTION_ID"  # select the intended Azure subscription
python3 azure/check_subscription.py --subscription "$SUBSCRIPTION_ID"  # require Enabled and spending limit On

# Verify remaining credit and expiry in the portal before proceeding; do not upgrade the offer.
export PRIVATE_DIR="$HOME/.local/state/tripilot-terraform"  # keep state, plans, and settings outside the project
mkdir -p "$PRIVATE_DIR" && chmod 700 "$PRIVATE_DIR"  # restrict access to the private working files
export TF_DATA_DIR="$PRIVATE_DIR/provider-data"  # keep backend metadata and provider binaries outside the project
export VAR_FILE="$PRIVATE_DIR/demo.tfvars"  # use the same non-secret settings file for all later plans
```

Create `demo.tfvars` in that private directory, using your real subscription UUID and a globally unique lowercase registry name:

```hcl
subscription_id        = "YOUR_AZURE_SUBSCRIPTION_UUID"
registry_name          = "youruniquetripilotregistry"
location               = "eastus"
resource_group_name    = "rg-tripilot-capstone3-tf"
name_prefix            = "tripilot-tf"
credit_offer_confirmed = true # only after checking the eligible offer, credit balance, and expiry
```

The subscription placeholder must be replaced. Check that the chosen region is allowed by your subscription. Do not place a raw API key in this settings file. Keep these resource names and the private state path unchanged across subsequent runs.

## 2. First-time infrastructure bootstrap

A private registry must exist before an application image can be pushed. The first apply therefore uses `bootstrap_only=true` to create infrastructure **without an app or a placeholder demo**.

Use this phase only for a fresh deployment/state. If the resource group or private state already exists, inspect its ownership and continue the existing deployment instead of re-running bootstrap blindly.

```bash
az provider register --namespace Microsoft.App --wait --subscription "$SUBSCRIPTION_ID"  # register Container Apps
az provider register --namespace Microsoft.ContainerRegistry --wait --subscription "$SUBSCRIPTION_ID"  # register ACR
az provider register --namespace Microsoft.ManagedIdentity --wait --subscription "$SUBSCRIPTION_ID"  # register managed identities
az provider register --namespace Microsoft.Network --wait --subscription "$SUBSCRIPTION_ID"  # register networking dependencies

docker build -t tripilot-app:terraform-demo .  # verify the actual app image builds locally before provisioning
terraform -chdir=terraform init -backend-config="path=$PRIVATE_DIR/terraform.tfstate"  # initialize a fresh private local backend
terraform -chdir=terraform validate          # check the Azure provider configuration and Terraform syntax
terraform -chdir=terraform plan -var-file="$VAR_FILE" -var='bootstrap_only=true'  # inspect only the initial infrastructure creation
terraform -chdir=terraform apply -var-file="$VAR_FILE" -var='bootstrap_only=true'  # review the fresh plan and type yes only if it matches the approved infrastructure
```

At this point, `app_url` is absent/null because no app exists yet. Do not claim a deployed application from the bootstrap result. Commit the generated `.terraform.lock.hcl` if maintaining this module; it records provider checksums and is not a state or secret file.

## 3. Publish the image and deploy the application

```bash
ACR_NAME="$(terraform -chdir=terraform output -raw registry_name)"  # read the created registry's resource name
ACR_SERVER="$(terraform -chdir=terraform output -raw registry_login_server)"  # read its actual hostname
az acr login --name "$ACR_NAME" --subscription "$SUBSCRIPTION_ID"  # authenticate Docker through Azure CLI, not an admin password
docker tag tripilot-app:terraform-demo "$ACR_SERVER/tripilot-app:step11"  # tag the tested app image
docker push "$ACR_SERVER/tripilot-app:step11"  # upload it to this deployment's private registry
DIGEST="$(az acr repository show --name "$ACR_NAME" --image tripilot-app:step11 --query digest --output tsv --subscription "$SUBSCRIPTION_ID")"  # resolve the immutable image digest
printf 'container_image = "%s/tripilot-app@%s"\n' "$ACR_SERVER" "$DIGEST"  # print the non-secret image setting to add to demo.tfvars
```

Add the printed `container_image` line to `demo.tfvars` **once**, or replace its existing value when updating. Do not add `bootstrap_only=true` to that persistent file. Normal deployments use the default `bootstrap_only=false`.

```bash
python3 azure/check_subscription.py --subscription "$SUBSCRIPTION_ID"  # recheck subscription protection before the application apply
terraform -chdir=terraform plan -var-file="$VAR_FILE"  # inspect the app, HTTPS ingress, identity, and health probes
terraform -chdir=terraform apply -var-file="$VAR_FILE"  # review the fresh plan and confirm the application deployment interactively
APP_URL="$(terraform -chdir=terraform output -raw app_url)"  # obtain the actual public Azure URL
printf '%s\n' "$APP_URL"                     # display the URL without any credentials
curl -fsS --retry 5 --retry-delay 5 --retry-all-errors --max-time 90 "$APP_URL/healthz" && echo  # verify HTTPS health, allowing a cold start
```

**Never set `bootstrap_only=true` after the app exists:** it would plan to remove the app. Review every plan before applying. If `container_image` is missing in normal mode, the configuration stops rather than deploying a sample image.

Open the actual URL, submit a cited request, inspect the visible model mode, and test feedback/monitoring. A configuration file or a successful bootstrap is not proof that the app is working.

## 4. Optional live Groq

The default deployment uses labelled mock mode. Enable live calls only after checking the selected Groq organization's **Free plan**, available models, and quota. The example model IDs are Groq-hosted `openai/gpt-oss-20b`; they do not require an Azure OpenAI account. Verify the current client implementation and model access using the [Azure/Groq guide](../azure/README-azure.md).

Add these **non-secret** settings to your private `demo.tfvars` only after those checks:

```hcl
enable_live_groq         = true
groq_free_plan_confirmed = true
answer_model            = "openai/gpt-oss-20b"
judge_model             = "openai/gpt-oss-20b"
```

Then supply the key privately. **State and saved plans will contain it; `sensitive` is not encryption.** Do not screenshot the credential-entry step or enable Terraform debug logging.

```bash
(                                           # keep the key scoped to this terminal subprocess
set -euo pipefail                            # stop if the live update fails
set +x                                      # do not echo expanded credential values
unset TF_LOG TF_LOG_PATH                     # avoid writing credential-bearing Terraform debug logs
read -r -s -p 'Groq API key: ' TF_VAR_groq_api_key  # enter the key without displaying it
printf '\n'                                 # move to a new line without printing the key
export TF_VAR_groq_api_key                   # supply the sensitive variable through the environment
trap 'unset TF_VAR_groq_api_key' EXIT        # clear the subprocess key when finished
terraform -chdir=terraform plan -var-file="$VAR_FILE"  # inspect the redacted live-mode plan; do not save it into Git
terraform -chdir=terraform apply -var-file="$VAR_FILE"  # apply only after reviewing and approving the live configuration
)                                           # leave the parent shell's environment unchanged
```

For subsequent live-mode updates, provide the key again without changing resource names or state location. The app receives `GROQ_API_KEY` through a Container Apps secret reference, not a Docker build argument. Protect the Terraform state and any earlier plans until securely disposed of after resource cleanup.

## Outputs and cleanup

`outputs.tf` now exposes Azure-specific values: `resource_group_name`, `registry_name`, `registry_login_server`, `container_app_environment_id`, `image_pull_identity_id`, `app_name`, `app_url`, and `subscription_spending_limit`. No API key is an output.

Before cleanup, retain any cloud records needed for review. The SQLite/JSONL files are ephemeral and are not the local Kind/Compose PostgreSQL store. Keep the state and settings until Terraform has removed the resources it owns.

```bash
terraform -chdir=terraform state list        # inspect the resources owned by this private Terraform state
# terraform -chdir=terraform destroy -var-file="$VAR_FILE" -var='enable_live_groq=false'  # DESTRUCTIVE: remove only this Terraform deployment after backup/review and explicit confirmation
```

Do not delete the local Kind cluster or the Streamlit Community Cloud app as part of this cleanup. Do not erase Terraform state to make resources disappear from a plan. A live Streamlit demo and an Azure deployment are separate hosting environments.
