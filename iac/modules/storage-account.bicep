// Azure Storage Account module for caching extraction results
// Supports both public access (with RBAC) and VNet integration modes

@description('Storage account name')
param storageAccountName string

@description('Location for the storage account')
param location string

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS'])
param sku string = 'Standard_LRS'

@description('Container name for extraction cache')
param cacheContainerName string = 'extraction-cache'

@description('Subnet resource ID to allow access from (Container Apps subnet). Leave empty for public access.')
param allowedSubnetId string = ''

@description('IP addresses to allow access from (for Container Apps without custom VNet)')
param allowedIpAddresses array = []

@description('Allow public network access. Set to false only when VNet/IP rules are configured.')
param allowPublicAccess bool = true

@description('Principal ID to grant Storage Blob Data Contributor role')
param blobContributorPrincipalId string = ''

@description('Tags to apply to resources')
param tags object = {}

// Determine if we have network restrictions
var hasNetworkRules = !empty(allowedSubnetId) || !empty(allowedIpAddresses)

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false  // Force Azure AD authentication (Managed Identity)
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: allowPublicAccess ? 'Enabled' : (hasNetworkRules ? 'Enabled' : 'Disabled')
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: hasNetworkRules ? 'Deny' : 'Allow'
      virtualNetworkRules: !empty(allowedSubnetId) ? [
        {
          id: allowedSubnetId
          action: 'Allow'
        }
      ] : []
      ipRules: [for ip in allowedIpAddresses: {
        value: ip
        action: 'Allow'
      }]
    }
  }
}

// Blob Services
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// Cache Container
resource cacheContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: cacheContainerName
  properties: {
    publicAccess: 'None'
  }
}

// Storage Blob Data Contributor role assignment
// Role ID: ba92f5b4-2d11-453d-a403-e96b0029c9fe
resource blobContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(blobContributorPrincipalId)) {
  name: guid(storageAccount.id, blobContributorPrincipalId, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    principalId: blobContributorPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

@description('Storage account name')
output name string = storageAccount.name

@description('Storage account resource ID')
output id string = storageAccount.id

@description('Blob endpoint')
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Cache container name')
output containerName string = cacheContainer.name
