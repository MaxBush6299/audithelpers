# AI Calibration Infrastructure Deployment

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Bicep CLI](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/install) installed (or use Azure CLI which includes it)
- [Docker](https://docs.docker.com/get-docker/) installed (for building container image)
- An active Azure subscription

## Resources Deployed

| Resource | Description |
|----------|-------------|
| **Azure OpenAI** | GPT-4.1/5.1 vision models for multimodal text extraction |
| **Document Intelligence** | OCR for embedded images (Form Recognizer) |
| **Container Registry** | Docker image registry for the Streamlit app |
| **Container App** | Serverless container hosting for the web UI |

## Deployment Workflow

The deployment is done in two phases:
1. **Phase 1**: Deploy backend infrastructure (Storage, AI services, Container Registry)
2. **Phase 2**: Build and push Docker image, then deploy Container App

### Phase 1: Deploy Backend Infrastructure

#### 1. Login to Azure

```powershell
az login
az account set --subscription "<your-subscription-id>"
```

#### 2. Create Resource Group

```powershell
$resourceGroup = "rg-ai-calibration-dev"
$location = "eastus"  # Recommended for Azure OpenAI and Document Intelligence

az group create --name $resourceGroup --location $location
```

> **Note:** Azure OpenAI is available in select regions. Check [Azure OpenAI regional availability](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability) for GPT-4.1/5.1 model availability.

#### 3. Deploy Infrastructure (Phase 1)

```powershell
cd iac

# Development
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/dev.bicepparam

# Or Production
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/prod.bicepparam
```

#### 4. Deploy GPT Models

After the Azure OpenAI resource is created, deploy the GPT models:

```powershell
# Get the AI Services name from deployment output
$aiServicesName = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.aiServicesName.value -o tsv)

# Deploy GPT-4.1 model (check Azure portal for available model versions)
az cognitiveservices account deployment create `
  --name $aiServicesName `
  --resource-group $resourceGroup `
  --deployment-name "gpt-41" `
  --model-name "gpt-4" `
  --model-version "turbo-2024-04-09" `
  --model-format OpenAI `
  --sku-capacity 10 `
  --sku-name Standard
```

### Phase 2: Build and Deploy Container App

#### 5. Build and Push Docker Image

```powershell
# Get ACR login server from deployment
$acrName = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.acrName.value -o tsv)

$acrLoginServer = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.acrLoginServer.value -o tsv)

# Login to ACR
az acr login --name $acrName

# Build and push image using ACR (from project root, not iac folder)
cd ..
az acr build --registry $acrName --image calibration-app:latest .
```

#### 6. Deploy Container App

Update the parameter file with the container image, then redeploy:

```powershell
cd iac

# Redeploy with Container App enabled
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/dev.bicepparam `
  --parameters deployContainerApp=true `
  --parameters containerImage="$acrLoginServer/calibration-app:latest"
```

#### 7. Get Application URL

```powershell
$appUrl = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.containerAppUrl.value -o tsv)

Write-Host "Application URL: $appUrl"
```

## Quick Deploy Script

For convenience, here's a complete deployment script:

```powershell
# Configuration
$resourceGroup = "rg-ai-calibration-dev"
$location = "eastus"
$environment = "dev"  # or "prod"

# Create resource group
az group create --name $resourceGroup --location $location

# Deploy Phase 1 (backend infrastructure)
cd iac
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/$environment.bicepparam

# Get outputs
$outputs = az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs -o json | ConvertFrom-Json

$acrName = $outputs.acrName.value
$acrLoginServer = $outputs.acrLoginServer.value
$aiServicesName = $outputs.aiServicesName.value

# Deploy GPT model
az cognitiveservices account deployment create `
  --name $aiServicesName `
  --resource-group $resourceGroup `
  --deployment-name "gpt-41" `
  --model-name "gpt-4" `
  --model-version "turbo-2024-04-09" `
  --model-format OpenAI `
  --sku-capacity 10 `
  --sku-name Standard

# Build and push container image
cd ..
az acr build --registry $acrName --image calibration-app:latest .

# Deploy Phase 2 (Container App)
cd iac
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/$environment.bicepparam `
  --parameters deployContainerApp=true `
  --parameters containerImage="$acrLoginServer/calibration-app:latest"

# Get app URL
$appUrl = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.containerAppUrl.value -o tsv)

Write-Host "`n✅ Deployment complete!"
Write-Host "Application URL: $appUrl"
```

## File Structure

```
iac/
├── main.bicep                      # Main deployment template
├── modules/
│   ├── ai-services.bicep           # Azure OpenAI module
│   ├── document-intelligence.bicep # Document Intelligence module
│   ├── container-registry.bicep    # Container Registry module
│   └── container-app.bicep         # Container App module
├── parameters/
│   ├── dev.bicepparam              # Development parameters
│   └── prod.bicepparam             # Production parameters
└── README.md                       # This file
```

## Environment Variables

The Container App is automatically configured with these environment variables from the deployed resources:

| Variable | Source |
|----------|--------|
| `AZURE_AI_ENDPOINT` | Azure OpenAI endpoint |
| `AZURE_AI_API_KEY` | Azure OpenAI key (stored as secret) |
| `GPT_4_1_DEPLOYMENT` | GPT deployment name |
| `AZURE_DI_ENDPOINT` | Document Intelligence endpoint |
| `AZURE_DI_KEY` | Document Intelligence key (stored as secret) |

## Local Development

For local development, create a `.env` file with the deployed resource values:

```powershell
# Get outputs
$outputs = az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs -o json | ConvertFrom-Json

# Get keys after deployment
$aiKey = az cognitiveservices account keys list `
  --name $outputs.aiServicesName.value `
  --resource-group $resourceGroup `
  --query key1 -o tsv

$diKey = az cognitiveservices account keys list `
  --name $outputs.documentIntelligenceName.value `
  --resource-group $resourceGroup `
  --query key1 -o tsv

# Create .env file
@"
AZURE_AI_ENDPOINT=$($outputs.aiServicesEndpoint.value)
AZURE_AI_API_KEY=$aiKey
GPT_4_1_DEPLOYMENT=gpt-41
AZURE_DI_ENDPOINT=$($outputs.documentIntelligenceEndpoint.value)
AZURE_DI_KEY=$diKey
"@ | Out-File -FilePath ../.env -Encoding utf8
```

## Customization

Edit the parameter files in `parameters/` to customize:

| Parameter | Description | Options |
|-----------|-------------|---------|
| `baseName` | Base name prefix for resources | Any string |
| `environment` | Environment identifier | `dev`, `staging`, `prod` |
| `aiServicesSku` | Azure OpenAI tier | `S0` (standard) |
| `documentIntelligenceSku` | Document Intelligence tier | `F0` (free), `S0` (standard) |
| `containerRegistrySku` | Container Registry tier | `Basic`, `Standard`, `Premium` |
| `containerCpu` | Container CPU cores | `0.5`, `1.0`, `2.0`, etc. |
| `containerMemory` | Container memory | `1Gi`, `2Gi`, `4Gi`, etc. |
| `deployContainerApp` | Deploy Container App | `true`, `false` |

## Using Azure AI Foundry Instead

If you're using **Azure AI Foundry** (AI Studio) instead of deploying your own Azure OpenAI resource:

1. Comment out the `aiServices` module in `main.bicep`
2. Get your endpoint and API key from Azure AI Foundry portal
3. Pass the values manually when deploying Container App

## Updating the Application

To update the application after code changes:

```powershell
# Rebuild and push new image
cd <project-root>
az acr build --registry $acrName --image calibration-app:latest .

# Restart the Container App to pull new image
az containerapp revision restart `
  --name aicalib-app-dev `
  --resource-group $resourceGroup
```

## Cleanup

To delete all resources:

```powershell
az group delete --name $resourceGroup --yes --no-wait
```

## Troubleshooting

### Container App not starting
- Check Container App logs: `az containerapp logs show --name aicalib-app-dev --resource-group $resourceGroup`
- Verify secrets are set correctly
- Ensure GPT model is deployed in Azure OpenAI

### Slide rendering issues
- The container uses LibreOffice for slide rendering (PowerPoint COM not available in Linux)
- Some complex slides may render differently than in PowerPoint

### Memory issues
- Increase `containerMemory` parameter if processing large PPTX files
- Default is 4Gi which should handle most files
