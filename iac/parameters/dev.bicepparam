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

// Set to true after pushing container image to ACR
param deployContainerApp = false
param containerImage = ''
