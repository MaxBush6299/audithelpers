// Azure Container Registry module

@description('Container Registry name')
param acrName string

@description('Location for the registry')
param location string

@description('SKU for Container Registry')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Tags to apply to the resource')
param tags object = {}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

@description('The login server for the registry')
output loginServer string = containerRegistry.properties.loginServer

@description('The registry name')
output name string = containerRegistry.name

@description('The registry resource ID')
output id string = containerRegistry.id
