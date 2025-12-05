# AI Calibration Infrastructure Deployment

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Bicep CLI](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/install) installed (or use Azure CLI which includes it)
- An active Azure subscription

## Resources Deployed

| Resource | Description |
|----------|-------------|
| **Storage Account** | Blob storage for temporary PPTX image uploads |
| **Azure OpenAI** | GPT-4.1/5.1 vision models for multimodal text extraction |
| **Document Intelligence** | OCR for embedded images (Form Recognizer) |

## Deployment

### 1. Login to Azure

```powershell
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create Resource Group

```powershell
$resourceGroup = "rg-ai-calibration-dev"
$location = "eastus"  # Recommended for Azure OpenAI and Document Intelligence

az group create --name $resourceGroup --location $location
```

> **Note:** Azure OpenAI is available in select regions. Check [Azure OpenAI regional availability](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability) for GPT-4.1/5.1 model availability.

### 3. Deploy Infrastructure

**Navigate to the iac folder first:**
```powershell
cd iac
```

**Development:**
```powershell
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/dev.bicepparam
```

**Production:**
```powershell
az deployment group create `
  --resource-group $resourceGroup `
  --template-file main.bicep `
  --parameters parameters/prod.bicepparam
```

### 4. Deploy GPT Models

After the Azure OpenAI resource is created, deploy the GPT models:

```powershell
# Get the AI Services name from deployment output
$aiServicesName = (az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs.aiServicesName.value -o tsv)

# Deploy GPT-4.1 model
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

> **Note:** Model names and versions may vary. Check Azure portal for available models in your region.

### 5. Retrieve Keys for .env File

After deployment, retrieve the keys:

```powershell
# Get deployment outputs
$outputs = az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs -o json | ConvertFrom-Json

# Get Storage Account connection string (already in outputs)
$storageConnectionString = $outputs.storageConnectionString.value

# Get Azure OpenAI key
$aiKey = az cognitiveservices account keys list `
  --name $outputs.aiServicesName.value `
  --resource-group $resourceGroup `
  --query 'key1' -o tsv

# Get Document Intelligence key
$diKey = az cognitiveservices account keys list `
  --name $outputs.documentIntelligenceName.value `
  --resource-group $resourceGroup `
  --query 'key1' -o tsv

# Display values for .env
Write-Host "=== Add these to your .env file ==="
Write-Host ""
Write-Host "# Azure Document Intelligence"
Write-Host "AZURE_DI_ENDPOINT=$($outputs.documentIntelligenceEndpoint.value)"
Write-Host "AZURE_DI_KEY=$diKey"
Write-Host ""
Write-Host "# Azure OpenAI (GPT-4.1)"
Write-Host "AZURE_AI_ENDPOINT=$($outputs.aiServicesEndpoint.value)"
Write-Host "AZURE_AI_API_KEY=$aiKey"
Write-Host "GPT_4_1_DEPLOYMENT=gpt-41"
Write-Host ""
Write-Host "# Azure Blob Storage (optional)"
Write-Host "AZURE_STORAGE_CONNECTION_STRING=$storageConnectionString"
```

## File Structure

```
iac/
├── main.bicep                      # Main deployment template
├── modules/
│   ├── storage.bicep               # Storage account module
│   ├── ai-services.bicep           # Azure OpenAI module
│   └── document-intelligence.bicep # Document Intelligence module
├── parameters/
│   ├── dev.bicepparam              # Development parameters
│   └── prod.bicepparam             # Production parameters
└── README.md                       # This file
```

## Customization

Edit the parameter files in `parameters/` to customize:

| Parameter | Description | Options |
|-----------|-------------|---------|
| `baseName` | Base name prefix for resources | Any string |
| `environment` | Environment identifier | `dev`, `staging`, `prod` |
| `storageSku` | Storage redundancy | `Standard_LRS`, `Standard_GRS`, `Standard_ZRS` |
| `aiServicesSku` | Azure OpenAI tier | `S0` (standard) |
| `documentIntelligenceSku` | Document Intelligence tier | `F0` (free), `S0` (standard) |

## Using Azure AI Foundry Instead

If you're using **Azure AI Foundry** (AI Studio) instead of deploying your own Azure OpenAI resource:

1. Skip the `ai-services.bicep` deployment or comment it out
2. Get your endpoint and API key from Azure AI Foundry portal
3. Add to `.env`:
   ```
   AZURE_AI_ENDPOINT=https://<your-foundry-project>.services.ai.azure.com
   AZURE_AI_API_KEY=<your-foundry-key>
   GPT_4_1_DEPLOYMENT=<your-deployment-name>
   ```

For GPT-5.1 (if deployed at a different endpoint):
```
AZURE_AI_GPT5_ENDPOINT=https://<your-gpt5-endpoint>.services.ai.azure.com
AZURE_AI_GPT5_API_KEY=<your-gpt5-key>
GPT_5_1_DEPLOYMENT=<your-gpt5-deployment-name>
```

## Cleanup

To delete all resources:

```powershell
az group delete --name $resourceGroup --yes --no-wait
```
