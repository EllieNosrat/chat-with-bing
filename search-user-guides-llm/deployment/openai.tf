provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "example" {
  name     = "dgtest0714rg"
  location = "South Central US"
}

resource "azurerm_cognitive_account" "example" {
  name                = "dgtest0714openai"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  kind                = "OpenAI"
  sku_name            = "S0"
}

resource "azurerm_openai_deployment" "example" {
  name                = "gpt-4o"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  cognitive_account_name = azurerm_cognitive_account.example.name
  model_name          = "gpt-4o"
  model_version       = "2024-10-21"
  deployment_type     = "Standard"
  rate_limit_tokens_per_minute = 100000
  rate_limit_requests_per_minute = 600
  endpoint_target_uri = "https://dgiar-m8dwd0ae-southcentralus.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21"
  api_key             = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
