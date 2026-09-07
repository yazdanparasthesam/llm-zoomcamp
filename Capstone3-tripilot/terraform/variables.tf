variable "subscription_id" {
  description = "Azure subscription UUID. Authenticate with Azure CLI; this is not an API key."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.subscription_id))
    error_message = "subscription_id must be an Azure subscription UUID."
  }
}

variable "location" {
  description = "Azure region allowed by the subscription and supporting Container Apps and ACR."
  type        = string
  default     = "eastus"
  nullable    = false

  validation {
    condition     = length(trimspace(var.location)) > 0
    error_message = "location must not be empty."
  }
}

variable "resource_group_name" {
  description = "Dedicated Terraform-owned group. Do not reuse the CLI/Bicep group's name or another project's group."
  type        = string
  default     = "rg-tripilot-capstone3-tf"
  nullable    = false

  validation {
    condition     = can(regex("^[A-Za-z0-9_().-]{1,90}$", var.resource_group_name)) && !endswith(var.resource_group_name, ".")
    error_message = "Use a valid, dedicated Azure resource-group name, without a trailing period."
  }
}

variable "name_prefix" {
  description = "Lowercase prefix for the app, environment, and managed identity."
  type        = string
  default     = "tripilot-tf"
  nullable    = false

  validation {
    condition     = length(var.name_prefix) <= 20 && can(regex("^[a-z][a-z0-9]*(-[a-z0-9]+)*$", var.name_prefix))
    error_message = "Use at most 20 lowercase letters, digits, or single internal hyphens, beginning with a letter."
  }
}

variable "registry_name" {
  description = "Globally unique Azure Container Registry name: 5-50 lowercase letters/digits."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{4,49}$", var.registry_name))
    error_message = "registry_name must be 5-50 lowercase letters/digits and begin with a letter."
  }
}

variable "credit_offer_confirmed" {
  description = "Set true only after checking eligible Azure credits, remaining balance, and expiry. This attestation does not replace the subscription-state/spending-limit checks."
  type        = bool
  default     = false
  nullable    = false
}

variable "bootstrap_only" {
  description = "Initial bootstrap only: create infrastructure before the private image exists. Never set true after deploying the app, because that would plan to remove the app."
  type        = bool
  default     = false
  nullable    = false
}

variable "container_image" {
  description = "Immutable image in this module's ACR, e.g. registry.azurecr.io/tripilot-app@sha256:<64 lowercase hex digits>. Null is permitted only during bootstrap."
  type        = string
  default     = null

  validation {
    condition     = var.container_image == null ? true : can(regex("^[a-z0-9.-]+/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$", var.container_image))
    error_message = "container_image must be an ACR image reference pinned by a complete sha256 digest, not a mutable tag."
  }
}

variable "enable_live_groq" {
  description = "Enable the optional Groq secret and environment reference. False preserves the no-key mock workflow."
  type        = bool
  default     = false
  nullable    = false
}

variable "groq_api_key" {
  description = "Optional Groq key, supplied privately through TF_VAR_groq_api_key. Sensitive redacts CLI output; the key is still stored in Terraform state/plan files. Never commit those files."
  type        = string
  default     = ""
  sensitive   = true
  nullable    = false
}

variable "groq_free_plan_confirmed" {
  description = "Required when live Groq is enabled: confirm the selected organization is Free and the models are permitted. Azure credits do not pay Groq invoices."
  type        = bool
  default     = false
  nullable    = false
}

variable "answer_model" {
  description = "Groq-hosted answer model. Verify Free-plan access before enabling live calls."
  type        = string
  default     = "openai/gpt-oss-20b"
  nullable    = false

  validation {
    condition     = length(trimspace(var.answer_model)) > 0
    error_message = "answer_model must not be empty."
  }
}

variable "judge_model" {
  description = "Groq-hosted relevance-judge model; does not change the committed offline evaluation results."
  type        = string
  default     = "openai/gpt-oss-20b"
  nullable    = false

  validation {
    condition     = length(trimspace(var.judge_model)) > 0
    error_message = "judge_model must not be empty."
  }
}

variable "tags" {
  description = "Additional Azure tags; the module always sets its project/purpose/managed_by tags."
  type        = map(string)
  default     = {}
  nullable    = false
}
