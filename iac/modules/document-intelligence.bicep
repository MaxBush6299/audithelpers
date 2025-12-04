@description('Name of the Document Intelligence resource')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('SKU for Document Intelligence')
@allowed([
  'F0'  // Free tier
  'S0'  // Standard tier
])
param sku string = 'S0'

@description('Tags to apply to the resource')
param tags object = {}

// Document Intelligence (Form Recognizer) resource
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: name
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: sku
  }
  tags: tags
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@description('The endpoint URL for Document Intelligence')
output endpoint string = documentIntelligence.properties.endpoint

@description('The resource ID')
output id string = documentIntelligence.id

@description('The resource name')
output name string = documentIntelligence.name
