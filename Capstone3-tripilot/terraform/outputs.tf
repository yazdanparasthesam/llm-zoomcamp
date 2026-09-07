output "resource_group_name" {
  description = "Dedicated Azure resource group managed by this Terraform configuration."
  value       = azurerm_resource_group.tripilot.name
}

output "registry_name" {
  description = "ACR resource name for az acr login and repository commands."
  value       = azurerm_container_registry.tripilot.name
}

output "registry_login_server" {
  description = "Actual ACR hostname; use this output instead of constructing the hostname."
  value       = azurerm_container_registry.tripilot.login_server
}

output "container_app_environment_id" {
  description = "Azure Container Apps environment resource ID."
  value       = azurerm_container_app_environment.tripilot.id
}

output "image_pull_identity_id" {
  description = "User-assigned identity with AcrPull on this registry only."
  value       = azurerm_user_assigned_identity.image_pull.id
}

output "app_name" {
  description = "Container App name after application deployment; null during bootstrap."
  value       = try(azurerm_container_app.tripilot[0].name, null)
}

output "app_url" {
  description = "Stable public HTTPS app URL after deployment; null during bootstrap. Verify the live service before publishing the URL."
  value       = try("https://${azurerm_container_app.tripilot[0].ingress[0].fqdn}", null)
}

output "subscription_spending_limit" {
  description = "Reported Azure spending-limit state; this does not report remaining credit or expiry."
  value       = data.azurerm_subscription.selected.spending_limit
}
