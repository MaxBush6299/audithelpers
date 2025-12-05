// Parameters file for production environment
using '../main.bicep'

param baseName = 'aicalib'
param location = 'eastus'  // Recommended region for AI services
param environment = 'prod'
param storageSku = 'Standard_GRS'
param aiServicesSku = 'S0'
param documentIntelligenceSku = 'S0'
