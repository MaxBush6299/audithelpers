// Parameters file for production environment
using '../main.bicep'

param baseName = 'aicalib'
param location = 'eastus'  // Recommended for Content Understanding
param environment = 'prod'
param storageSku = 'Standard_GRS'
param aiServicesSku = 'S0'
