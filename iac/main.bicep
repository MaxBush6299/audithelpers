// Main deployment template for AI Calibration infrastructure
// Deploys: Container Registry, Container App
// Optionally creates or references existing AI services

targetScope = 'resourceGroup'

@description('Base name for all resources')
param baseName string = 'aicalib'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Existing Azure AI Services resource name. Leave empty to create new.')
param existingAiServicesName string = ''

@description('Existing Document Intelligence resource name. Leave empty to create new.')
param existingDocIntelligenceName string = ''

@description('Azure AI Services SKU (only used when creating new)')
@allowed(['S0', 'F0'])
param aiServicesSku string = 'S0'

@description('Document Intelligence SKU (only used when creating new)')
@allowed(['S0', 'F0'])
param documentIntelligenceSku string = 'S0'

@description('Deploy Container App (set to false for initial infra-only deployment)')
param deployContainerApp bool = false

@description('Container image to deploy (required if deployContainerApp is true)')
param containerImage string = ''

@description('Container Registry SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param containerRegistrySku string = 'Basic'

@description('CPU cores for Container App')
param containerCpu string = '2.0'

@description('Memory for Container App')
param containerMemory string = '4Gi'

@description('GPT-4.1 deployment name in Azure OpenAI')
param gptDeploymentName string = 'gpt-41'

@description('Azure OpenAI GPT-5.1 endpoint (optional, for separate GPT-5 deployment)')
@secure()
param azureAiGpt5Endpoint string = ''

@description('Azure OpenAI GPT-5.1 API key (optional)')
@secure()
param azureAiGpt5ApiKey string = ''

@description('GPT-5.1 deployment name (optional)')
param gpt5DeploymentName string = ''

@description('Deploy Storage Account for caching')
param deployStorageAccount bool = true

@description('Existing Storage Account name for caching. Leave empty to create new.')
param existingStorageAccountName string = ''

@description('Storage Account SKU (only used when creating new)')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS'])
param storageAccountSku string = 'Standard_LRS'

// Determine if using existing resources
var useExistingAi = !empty(existingAiServicesName)
var useExistingDi = !empty(existingDocIntelligenceName)
var useExistingStorage = !empty(existingStorageAccountName)

// Generate unique names for new resources
var uniqueSuffix = uniqueString(resourceGroup().id)
var newAiServicesName = '${baseName}-ai-${environment}-${uniqueSuffix}'
var newDocIntelligenceName = '${baseName}-di-${environment}-${uniqueSuffix}'
var newStorageAccountName = toLower('${baseName}cache${environment}${take(uniqueSuffix, 8)}')
var containerRegistryName = toLower('${baseName}acr${environment}${uniqueSuffix}')
var containerAppName = '${baseName}-app-${environment}'
var containerEnvName = '${baseName}-env-${environment}'

var tags = {
  environment: environment
  project: 'ai-calibration'
}

// Reference existing Azure AI Services (if provided)
resource existingAiServices 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' existing = if (useExistingAi) {
  name: existingAiServicesName
}

// Reference existing Document Intelligence (if provided)
resource existingDocIntelligence 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' existing = if (useExistingDi) {
  name: existingDocIntelligenceName
}

// Create new Azure AI Services (if not using existing)
module newAiServices 'modules/ai-services.bicep' = if (!useExistingAi) {
  name: 'ai-services-deployment'
  params: {
    aiServicesName: newAiServicesName
    location: location
    sku: aiServicesSku
  }
}

// Create new Document Intelligence (if not using existing)
module newDocIntelligence 'modules/document-intelligence.bicep' = if (!useExistingDi) {
  name: 'document-intelligence-deployment'
  params: {
    name: newDocIntelligenceName
    location: location
    sku: documentIntelligenceSku
    tags: tags
  }
}

// Resolve AI Services values (existing or new)
// Using non-null assertion (!) because we know the resource exists based on the condition
var aiEndpoint = useExistingAi 
  ? existingAiServices!.properties.endpoint 
  : newAiServices!.outputs.endpoint
var aiKey = useExistingAi 
  ? existingAiServices!.listKeys().key1 
  : newAiServices!.outputs.apiKey
var aiName = useExistingAi 
  ? existingAiServices!.name 
  : newAiServices!.outputs.name

// Resolve Document Intelligence values (existing or new)
var diEndpoint = useExistingDi 
  ? existingDocIntelligence!.properties.endpoint 
  : newDocIntelligence!.outputs.endpoint
var diKey = useExistingDi 
  ? existingDocIntelligence!.listKeys().key1 
  : newDocIntelligence!.outputs.apiKey
var diName = useExistingDi 
  ? existingDocIntelligence!.name 
  : newDocIntelligence!.outputs.name

// Resolve Storage Account name
var storageAccountName = useExistingStorage 
  ? existingStorageAccountName 
  : (deployStorageAccount ? newStorageAccountName : '')

// Azure Container Registry
module containerRegistry 'modules/container-registry.bicep' = {
  name: 'container-registry-deployment'
  params: {
    acrName: take(containerRegistryName, 50) // ACR names max 50 chars
    location: location
    sku: containerRegistrySku
    tags: tags
  }
}

// Container App (conditionally deployed)
// Always keep minReplicas:1 to avoid slow cold-start image pulls on scale-from-zero
module containerApp 'modules/container-app.bicep' = if (deployContainerApp && containerImage != '') {
  name: 'container-app-deployment'
  params: {
    containerAppName: containerAppName
    environmentName: containerEnvName
    location: location
    containerImage: containerImage
    acrName: containerRegistry.outputs.name
    cpu: containerCpu
    memory: containerMemory
    minReplicas: 1  // Keep warm to avoid cold-start timeouts with large images
    maxReplicas: environment == 'prod' ? 3 : 1
    azureAiEndpoint: aiEndpoint
    azureAiApiKey: aiKey
    gptDeploymentName: gptDeploymentName
    azureAiGpt5Endpoint: azureAiGpt5Endpoint
    azureAiGpt5ApiKey: azureAiGpt5ApiKey
    gpt5DeploymentName: gpt5DeploymentName
    documentIntelligenceEndpoint: diEndpoint
    documentIntelligenceKey: diKey
    storageAccountName: storageAccountName
    tags: tags
  }
}

// Storage Account for caching (deployed after Container App to get its principal ID)
// When using existing storage, just do the role assignment
module storageAccount 'modules/storage-account.bicep' = if (deployStorageAccount && !useExistingStorage) {
  name: 'storage-account-deployment'
  params: {
    storageAccountName: newStorageAccountName
    location: location
    sku: storageAccountSku
    // For managed Container Apps VNet, we allow public access but secure via RBAC
    // Set allowPublicAccess to false when using custom VNet with service endpoints
    allowPublicAccess: true
    blobContributorPrincipalId: deployContainerApp && containerImage != '' ? containerApp!.outputs.principalId : ''
    tags: tags
  }
}

// Role assignment for existing storage account
resource existingStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = if (useExistingStorage) {
  name: existingStorageAccountName
}

// Use a deterministic GUID based on resource names only (known at compile time)
// The role assignment name must be deterministic and not depend on runtime values
resource existingStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (useExistingStorage && deployContainerApp && containerImage != '') {
  name: guid(resourceGroup().id, existingStorageAccountName, containerAppName, 'StorageBlobDataContributor')
  scope: existingStorageAccount
  properties: {
    principalId: containerApp!.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

// Outputs for configuration
output aiServicesEndpoint string = aiEndpoint
output aiServicesName string = aiName

output documentIntelligenceEndpoint string = diEndpoint
output documentIntelligenceName string = diName

// Container Registry outputs
output acrLoginServer string = containerRegistry.outputs.loginServer
output acrName string = containerRegistry.outputs.name

// Container App outputs (conditional) - use non-null assertion since condition guarantees existence
output containerAppUrl string = deployContainerApp && containerImage != '' ? containerApp!.outputs.url : ''
output containerAppFqdn string = deployContainerApp && containerImage != '' ? containerApp!.outputs.fqdn : ''

// Storage Account outputs
output storageAccountName string = storageAccountName
output storageAccountBlobEndpoint string = deployStorageAccount && !useExistingStorage ? storageAccount!.outputs.blobEndpoint : (useExistingStorage ? 'https://${existingStorageAccountName}.blob.${az.environment().suffixes.storage}/' : '')
