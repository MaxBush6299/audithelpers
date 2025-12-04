// Main deployment template for AI Calibration infrastructure
// Deploys: Storage Account, Azure AI Services, Document Intelligence

targetScope = 'resourceGroup'

@description('Base name for all resources')
param baseName string = 'aicalib'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS'])
param storageSku string = 'Standard_LRS'

@description('Azure AI Services SKU')
@allowed(['S0', 'F0'])
param aiServicesSku string = 'S0'

@description('Document Intelligence SKU')
@allowed(['S0', 'F0'])
param documentIntelligenceSku string = 'S0'

// Generate unique names
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = toLower('${baseName}${environment}${uniqueSuffix}')
var aiServicesName = '${baseName}-ai-${environment}-${uniqueSuffix}'
var documentIntelligenceName = '${baseName}-di-${environment}-${uniqueSuffix}'
var containerName = 'pptx-tmp'

// Storage Account
module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    storageAccountName: take(storageAccountName, 24) // Storage account names max 24 chars
    location: location
    sku: storageSku
    containerName: containerName
  }
}

// Azure AI Services (Content Understanding)
module aiServices 'modules/ai-services.bicep' = {
  name: 'ai-services-deployment'
  params: {
    aiServicesName: aiServicesName
    location: location
    sku: aiServicesSku
  }
}

// Document Intelligence (Form Recognizer)
module documentIntelligence 'modules/document-intelligence.bicep' = {
  name: 'document-intelligence-deployment'
  params: {
    name: documentIntelligenceName
    location: location
    sku: documentIntelligenceSku
    tags: {
      environment: environment
      project: 'ai-calibration'
    }
  }
}

// Outputs for .env file configuration
output storageAccountName string = storage.outputs.storageAccountName
output storageConnectionString string = storage.outputs.connectionString
output storageBlobEndpoint string = storage.outputs.blobEndpoint
output containerName string = containerName

output aiServicesEndpoint string = aiServices.outputs.endpoint
output aiServicesName string = aiServices.outputs.name

output documentIntelligenceEndpoint string = documentIntelligence.outputs.endpoint
output documentIntelligenceName string = documentIntelligence.outputs.name

// Note: Keys should be retrieved separately using Azure CLI for security
// az storage account keys list --account-name <storageAccountName>
// az cognitiveservices account keys list --name <aiServicesName> --resource-group <resourceGroup>
// az cognitiveservices account keys list --name <documentIntelligenceName> --resource-group <resourceGroup>
