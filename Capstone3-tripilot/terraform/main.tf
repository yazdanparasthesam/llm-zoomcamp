terraform {
  required_version = ">= 1.9.0, < 2.0.0"

  # Supply a private, outside-repository state path during terraform init.
  backend "local" {}

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.81.0"
    }
  }
}

provider "azurerm" {
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "none"

  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

# Authentication uses the selected Azure CLI session (az login), not a model key.
# Provider registration is explicit in the README and never automatic here.
data "azurerm_subscription" "selected" {
  subscription_id = var.subscription_id
}

locals {
  tags = merge(var.tags, {
    project    = "tripilot"
    purpose    = "capstone3-demo"
    managed_by = "terraform"
  })
}

resource "azurerm_resource_group" "tripilot" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags

  lifecycle {
    precondition {
      condition     = var.credit_offer_confirmed
      error_message = "Confirm an eligible credit offer, remaining credit, and expiry before applying. Do not upgrade to Pay-As-You-Go for this credits-only deployment."
    }
    precondition {
      condition     = data.azurerm_subscription.selected.state == "Enabled" && data.azurerm_subscription.selected.spending_limit == "On"
      error_message = "Require an Enabled Azure subscription with spending limit On. This configuration will not remove a spending limit or change your subscription offer."
    }
    precondition {
      condition     = !var.enable_live_groq || (var.groq_free_plan_confirmed && length(trimspace(var.groq_api_key)) > 0)
      error_message = "Live Groq requires a privately supplied API key and a separately confirmed Groq Free organization. Azure credits do not cover Groq bills."
    }
  }
}

resource "azurerm_container_registry" "tripilot" {
  name                                         = var.registry_name
  resource_group_name                          = azurerm_resource_group.tripilot.name
  location                                     = azurerm_resource_group.tripilot.location
  sku                                          = "Standard"
  admin_enabled                                = false
  role_assignment_mode                         = "LegacyRegistryPermissions"
  public_network_access_enabled                = true
  azuread_authentication_as_arm_policy_enabled = true
  tags                                         = local.tags
}

resource "azurerm_user_assigned_identity" "image_pull" {
  name                = "${var.name_prefix}-acr-pull"
  resource_group_name = azurerm_resource_group.tripilot.name
  location            = azurerm_resource_group.tripilot.location
  tags                = local.tags
}

resource "azurerm_role_assignment" "image_pull" {
  scope                            = azurerm_container_registry.tripilot.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_user_assigned_identity.image_pull.principal_id
  skip_service_principal_aad_check = true
}

resource "azurerm_container_app_environment" "tripilot" {
  name                = "${var.name_prefix}-env"
  resource_group_name = azurerm_resource_group.tripilot.name
  location            = azurerm_resource_group.tripilot.location
  tags                = local.tags

  # Omitting workload profiles creates a Consumption-only environment.
  # Omitting logs_destination and workspace ID keeps log streaming only;
  # no Log Analytics workspace, private endpoint, or dedicated profile is created.
}

resource "azurerm_container_app" "tripilot" {
  count = var.bootstrap_only ? 0 : 1

  name                         = "${var.name_prefix}-app"
  resource_group_name          = azurerm_resource_group.tripilot.name
  container_app_environment_id = azurerm_container_app_environment.tripilot.id
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.image_pull.id]
  }

  registry {
    server   = azurerm_container_registry.tripilot.login_server
    identity = azurerm_user_assigned_identity.image_pull.id
  }

  # Optional. A sensitive Terraform variable is redacted in CLI output but
  # its value is still stored in Terraform state/plan files; protect those files.
  dynamic "secret" {
    for_each = var.enable_live_groq ? [1] : []
    content {
      name  = "groq-api-key"
      value = var.groq_api_key
    }
  }

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name = "tripilot"
      # The placeholder is blocked by the precondition below and is never a demo image.
      image  = coalesce(var.container_image, "invalid.example.invalid/tripilot:not-configured")
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "LLM_PROVIDER"
        value = "groq"
      }
      env {
        name  = "TRIPILOT_MODEL_ANSWER"
        value = var.answer_model
      }
      env {
        name  = "TRIPILOT_MODEL_JUDGE"
        value = var.judge_model
      }
      env {
        name  = "TRIPILOT_SQLITE"
        value = "/app/data/tripilot_monitoring.db"
      }
      env {
        name  = "TRIPILOT_QUERY_LOG"
        value = "/app/data/query_log.jsonl"
      }
      dynamic "env" {
        for_each = var.enable_live_groq ? [1] : []
        content {
          name        = "GROQ_API_KEY"
          secret_name = "groq-api-key"
        }
      }

      startup_probe {
        transport               = "HTTP"
        port                    = 8501
        path                    = "/healthz"
        initial_delay           = 5
        interval_seconds        = 5
        timeout                 = 3
        failure_count_threshold = 60
      }
      readiness_probe {
        transport               = "HTTP"
        port                    = 8501
        path                    = "/healthz"
        interval_seconds        = 10
        timeout                 = 3
        failure_count_threshold = 3
      }
      liveness_probe {
        transport               = "HTTP"
        port                    = 8501
        path                    = "/healthz"
        initial_delay           = 60
        interval_seconds        = 30
        timeout                 = 5
        failure_count_threshold = 3
      }
    }
  }

  ingress {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8501
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  depends_on = [azurerm_role_assignment.image_pull]

  lifecycle {
    precondition {
      condition     = var.container_image != null
      error_message = "Set container_image to the pushed ACR image digest. Use bootstrap_only=true only for the initial infrastructure bootstrap, before an app exists."
    }
    precondition {
      condition     = var.container_image == null ? true : startswith(var.container_image, "${azurerm_container_registry.tripilot.login_server}/")
      error_message = "The app image must come from this deployment's Azure Container Registry. Read registry_login_server from Terraform outputs."
    }
  }
}
