// Parameters file for production environment
using '../main.bicep'

param baseName = 'aicalib'
param location = 'eastus'
param environment = 'prod'

// Leave empty to create new AI resources, or specify existing resource names
param existingAiServicesName = ''
param existingDocIntelligenceName = ''

// SKUs for new resources (ignored if using existing)
param aiServicesSku = 'S0'
param documentIntelligenceSku = 'S0'

// Container App settings
param containerRegistrySku = 'Standard'  // Standard for production
param containerCpu = '2.0'
param containerMemory = '4Gi'
param gptDeploymentName = 'gpt-41'

// Set to true after pushing container image to ACR
param deployContainerApp = false
param containerImage = ''
