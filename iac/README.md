# AI Calibration Infrastructure Deployment

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Bicep CLI](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/install) installed (or use Azure CLI which includes it)
- An active Azure subscription

## Resources Deployed

| Resource | Description |
|----------|-------------|
| **Storage Account** | Blob storage for temporary PPTX image uploads |
| **Azure AI Services** | Multi-service cognitive account (includes Content Understanding) |

## Deployment

### 1. Login to Azure

```powershell
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create Resource Group

```powershell
$resourceGroup = "rg-ai-calibration-dev"
$location = "eastus"  # Recommended for Content Understanding

az group create --name $resourceGroup --location $location
```

> **Note:** Content Understanding is available in: `eastus`, `eastus2`, `westus`, `westus3`, `southcentralus`, `northeurope`, `westeurope`, `swedencentral`, `uksouth`, `southeastasia`, `japaneast`, `australiaeast`

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

### 4. Retrieve Keys for .env File

After deployment, retrieve the keys:

```powershell
# Get deployment outputs
$outputs = az deployment group show `
  --resource-group $resourceGroup `
  --name main `
  --query properties.outputs -o json | ConvertFrom-Json

# Get Storage Account key
$storageKey = az storage account keys list `
  --account-name $outputs.storageAccountName.value `
  --query '[0].value' -o tsv

# Get AI Services key
$aiKey = az cognitiveservices account keys list `
  --name $outputs.aiServicesName.value `
  --resource-group $resourceGroup `
  --query 'key1' -o tsv

# Display values for .env
Write-Host "=== Add these to your .env file ==="
Write-Host "AZURE_STORAGE_CONNECTION_STRING=$($outputs.storageConnectionString.value)"
Write-Host "AZURE_CU_ENDPOINT=$($outputs.aiServicesEndpoint.value)"
Write-Host "AZURE_CU_KEY=$aiKey"
```

## File Structure

```
iac/
├── main.bicep              # Main deployment template
├── modules/
│   ├── storage.bicep       # Storage account module
│   └── ai-services.bicep   # Azure AI Services module
├── parameters/
│   ├── dev.bicepparam      # Development parameters
│   └── prod.bicepparam     # Production parameters
└── README.md               # This file
```

## Customization

Edit the parameter files in `parameters/` to customize:

- `baseName` - Base name prefix for resources
- `environment` - Environment identifier (dev/staging/prod)
- `storageSku` - Storage redundancy (Standard_LRS, Standard_GRS, Standard_ZRS)
- `aiServicesSku` - AI Services tier (F0 for free, S0 for standard)

## Cleanup

To delete all resources:

```powershell
az group delete --name $resourceGroup --yes --no-wait
```
