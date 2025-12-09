// Azure Container Apps module for Streamlit web application

@description('Container App name')
param containerAppName string

@description('Container Apps Environment name')
param environmentName string

@description('Location for resources')
param location string

@description('Container image to deploy')
param containerImage string

@description('Azure Container Registry name (without .azurecr.io)')
param acrName string = ''

@description('CPU cores for the container')
param cpu string = '2.0'

@description('Memory for the container (e.g., 4Gi)')
param memory string = '4Gi'

@description('Minimum number of replicas')
param minReplicas int = 0

@description('Maximum number of replicas')
param maxReplicas int = 1

@description('Azure OpenAI endpoint')
@secure()
param azureAiEndpoint string

@description('Azure OpenAI API key')
@secure()
param azureAiApiKey string

@description('GPT deployment name')
param gptDeploymentName string = 'gpt-41'

@description('Document Intelligence endpoint')
@secure()
param documentIntelligenceEndpoint string

@description('Document Intelligence key')
@secure()
param documentIntelligenceKey string

@description('Tags to apply to resources')
param tags object = {}

// Log Analytics Workspace for Container Apps Environment
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${environmentName}-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8501
        transport: 'auto'
        allowInsecure: false
      }
      registries: acrName != '' ? [
        {
          server: '${acrName}.azurecr.io'
          identity: 'system'
        }
      ] : []
      secrets: [
        {
          name: 'azure-ai-endpoint'
          value: azureAiEndpoint
        }
        {
          name: 'azure-ai-key'
          value: azureAiApiKey
        }
        {
          name: 'di-endpoint'
          value: documentIntelligenceEndpoint
        }
        {
          name: 'di-key'
          value: documentIntelligenceKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'calibration-app'
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            {
              name: 'AZURE_AI_ENDPOINT'
              secretRef: 'azure-ai-endpoint'
            }
            {
              name: 'AZURE_AI_API_KEY'
              secretRef: 'azure-ai-key'
            }
            {
              name: 'GPT_4_1_DEPLOYMENT'
              value: gptDeploymentName
            }
            {
              name: 'AZURE_DI_ENDPOINT'
              secretRef: 'di-endpoint'
            }
            {
              name: 'AZURE_DI_KEY'
              secretRef: 'di-key'
            }
            {
              name: 'PYTHONUNBUFFERED'
              value: '1'
            }
          ]
          // Add startup probe with much longer timeout for large image with LibreOffice (~700MB)
          // LibreOffice installation can take significant time to initialize on first run
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/_stcore/health'
                port: 8501
              }
              initialDelaySeconds: 60      // Wait 1 minute before first check
              periodSeconds: 15            // Check every 15 seconds
              failureThreshold: 40         // 40 * 15s = 10 minutes total startup time
              timeoutSeconds: 10           // Allow 10 seconds per check
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/_stcore/health'
                port: 8501
              }
              initialDelaySeconds: 0       // Starts after startup probe succeeds
              periodSeconds: 30
              failureThreshold: 3
              timeoutSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Grant Container App access to ACR
resource acrResource 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = if (acrName != '') {
  name: acrName
}

// ACR Pull role assignment for Container App's managed identity
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (acrName != '') {
  name: guid(containerApp.id, acrResource.id, 'acrpull')
  scope: acrResource
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull role
  }
}

@description('The FQDN of the Container App')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('The URL of the Container App')
output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('The Container App resource ID')
output id string = containerApp.id

@description('The Container App name')
output name string = containerApp.name

@description('The Container Apps Environment ID')
output environmentId string = containerAppsEnvironment.id
