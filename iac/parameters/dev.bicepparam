// Parameters file for development environment
using '../main.bicep'

param baseName = 'aicalib'
param location = 'eastus'
param environment = 'dev'

// Use existing AI resources (set to empty string '' to create new)
param existingAiServicesName = 'ai-calibration-dev-resource'
param existingDocIntelligenceName = 'aicalib-di-dev-7oav7uq2qtryk'

// SKUs for new resources (ignored if using existing)
param aiServicesSku = 'S0'
param documentIntelligenceSku = 'S0'

// Container App settings
param containerRegistrySku = 'Basic'
param containerCpu = '2.0'
param containerMemory = '4Gi'
param gptDeploymentName = 'gpt-41'

// GPT-5.1 settings (optional - set these if you have a separate GPT-5 deployment)
// These are passed via deployment command: --parameters azureAiGpt5Endpoint='...' azureAiGpt5ApiKey='...'
param gpt5DeploymentName = ''

// Set to true after pushing container image to ACR
param deployContainerApp = false
param containerImage = ''
