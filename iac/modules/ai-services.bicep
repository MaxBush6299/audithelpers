// Azure OpenAI Services module (for GPT-4.1/5.1 vision models)

@description('Azure OpenAI Services account name')
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
  kind: 'OpenAI' // Azure OpenAI for GPT-4.1/5.1 vision models
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
output apiKey string = aiServices.listKeys().key1
