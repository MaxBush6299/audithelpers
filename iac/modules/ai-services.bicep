// Azure AI Services module (Content Understanding)

@description('Azure AI Services account name')
param aiServicesName string

@description('Location for the AI Services account')
param location string

@description('SKU for AI Services')
param sku string

resource aiServices 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: aiServicesName
  location: location
  sku: {
    name: sku
  }
  kind: 'CognitiveServices' // Multi-service account that includes Content Understanding
  properties: {
    customSubDomainName: aiServicesName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

output name string = aiServices.name
output endpoint string = aiServices.properties.endpoint
output id string = aiServices.id
