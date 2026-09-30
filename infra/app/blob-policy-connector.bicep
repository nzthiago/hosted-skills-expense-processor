@description('Name of the Connector Namespace.')
param name string

param location string = resourceGroup().location
param tags object = {}

@description('Object ID of the Function app user-assigned managed identity.')
param functionPrincipalId string

@description('Object ID of the deploying user for connector authorization and local MCP testing.')
param developerPrincipalId string = ''

@description('Entra tenant ID used by connection access policies.')
param tenantId string = tenant().tenantId

@description('Storage account containing the policy documents.')
param storageAccountName string

@description('Blob container containing the policy documents.')
param policyContainerName string

@description('Dataverse entity set name used by the Update a row operation.')
param dataverseEntitySetName string = 'hep_expenserequests'

@description('Dataverse environment URL used by the Update a row operation.')
param dataverseEnvironmentUrl string

@description('Name of the Azure Blob connection.')
param blobConnectionName string = 'blob-policy-reader'

@description('Name of the Dataverse connection.')
param dataverseConnectionName string = 'dataverse-expense-requests'

@description('Name of the Blob policy MCP server.')
param policyMcpServerName string = 'Blob-policy-reader'

@description('Name of the Dataverse update MCP server.')
param dataverseMcpServerName string = 'Dataverse-expense-updater'

var storageBlobDataReaderRoleDefinitionId = '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'

#disable-next-line BCP081
resource connectorNamespace 'Microsoft.Web/connectorGateways@2026-05-01-preview' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

#disable-next-line BCP081
resource blobConnection 'Microsoft.Web/connectorGateways/connections@2026-05-01-preview' = {
  parent: connectorNamespace
  name: blobConnectionName
  properties: {
    connectorName: 'azureblob'
    displayName: 'Expense Policy Blob Reader'
    parameterValueSet: {
      name: 'managedIdentityAuth'
      values: {}
    }
  }
}

#disable-next-line BCP081
resource dataverseConnection 'Microsoft.Web/connectorGateways/connections@2026-05-01-preview' = {
  parent: connectorNamespace
  name: dataverseConnectionName
  properties: {
    connectorName: 'commondataservice'
    displayName: 'Expense Request Dataverse'
  }
}

#disable-next-line BCP081
resource namespaceBlobAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = {
  parent: blobConnection
  name: 'namespace-policy-reader'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: connectorNamespace.identity.principalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource functionBlobAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = {
  parent: blobConnection
  name: 'function-policy-reader'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: functionPrincipalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource developerBlobAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = if (!empty(developerPrincipalId)) {
  parent: blobConnection
  name: 'developer-policy-reader'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: developerPrincipalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource namespaceDataverseAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = {
  parent: dataverseConnection
  name: 'namespace-expense-updater'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: connectorNamespace.identity.principalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource functionDataverseAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = {
  parent: dataverseConnection
  name: 'function-expense-updater'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: functionPrincipalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource developerDataverseAccessPolicy 'Microsoft.Web/connectorGateways/connections/accessPolicies@2026-05-01-preview' = if (!empty(developerPrincipalId)) {
  parent: dataverseConnection
  name: 'developer-expense-updater'
  properties: {
    principal: {
      type: 'ActiveDirectory'
      identity: {
        objectId: developerPrincipalId
        tenantId: tenantId
      }
    }
  }
}

#disable-next-line BCP081
resource policyMcpServer 'Microsoft.Web/connectorGateways/mcpServerConfigs@2026-05-01-preview' = {
  parent: connectorNamespace
  name: policyMcpServerName
  properties: {
    description: 'Read-only access to expense policy documents in Azure Blob Storage.'
    state: 'Enabled'
    disableApiKeyAuth: true
    settings: {
      textOnlyContent: true
    }
    policies: []
    connectors: [
      {
        connectionName: blobConnection.name
        name: 'azureblob'
        displayName: 'Azure Blob Storage'
        description: 'Lists and reads expense policy documents.'
        operations: [
          {
            name: 'ListFolder_V4'
            displayName: 'List expense policy documents'
            description: 'List the expense policy documents.'
            userParameters: [
              {
                name: 'dataset'
                value: storageAccountName
              }
              {
                name: 'id'
                value: policyContainerName
              }
            ]
            agentParameters: []
          }
          {
            name: 'GetFileContentByPath_V2'
            displayName: 'Read expense policy document'
            description: 'Read one Markdown expense policy document by its full Blob path.'
            userParameters: [
              {
                name: 'dataset'
                value: storageAccountName
              }
            ]
            agentParameters: [
              {
                name: 'path'
                schema: {
                  type: 'string'
                  required: true
                  description: 'Full Blob path, for example /${policyContainerName}/travel-policy.md.'
                }
              }
            ]
          }
        ]
      }
    ]
  }
  dependsOn: [
    namespaceBlobAccessPolicy
    functionBlobAccessPolicy
    developerBlobAccessPolicy
  ]
}

#disable-next-line BCP081
resource dataverseMcpServer 'Microsoft.Web/connectorGateways/mcpServerConfigs@2026-05-01-preview' = {
  parent: connectorNamespace
  name: dataverseMcpServerName
  properties: {
    description: 'Update the decision fields on the source Dataverse Expense Request row.'
    state: 'Enabled'
    disableApiKeyAuth: true
    settings: {
      textOnlyContent: true
    }
    policies: []
    connectors: [
      {
        connectionName: dataverseConnection.name
        name: 'commondataservice'
        displayName: 'Microsoft Dataverse'
        description: 'Updates one existing Expense Request row.'
        operations: [
          {
            name: 'PatchItem_V2'
            displayName: 'Update expense request'
            description: 'Update the decision fields on the source Expense Request row.'
            userParameters: [
              {
                name: 'dataset'
                value: dataverseEnvironmentUrl
              }
              {
                name: 'table'
                value: dataverseEntitySetName
              }
            ]
            agentParameters: [
              {
                name: 'id'
                schema: {
                  type: 'string'
                  required: true
                  description: 'Dataverse GUID from source.row_id.'
                }
              }
              {
                name: 'item'
                schema: {
                  type: 'object'
                  required: true
                  description: 'Decision fields: hep_decision, hep_reason, hep_policyapplied, and hep_processedon.'
                  properties: {
                    hep_decision: {
                      type: 'string'
                      enum: [
                        'Approved'
                        'Needs Review'
                        'Flagged'
                      ]
                    }
                    hep_reason: {
                      type: 'string'
                      maxLength: 90
                      description: 'One-sentence explanation with at most 90 characters.'
                    }
                    hep_policyapplied: {
                      type: 'string'
                    }
                    hep_processedon: {
                      type: 'string'
                      description: 'Current UTC time in compact ISO 8601 basic format YYYYMMDDTHHMMSSZ, without colons.'
                    }
                  }
                }
              }
            ]
          }
        ]
      }
    ]
  }
  dependsOn: [
    namespaceDataverseAccessPolicy
    functionDataverseAccessPolicy
    developerDataverseAccessPolicy
  ]
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource policyContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  parent: blobService
  name: policyContainerName
}

resource connectorPolicyReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(policyContainer.id, connectorNamespace.name, storageBlobDataReaderRoleDefinitionId)
  scope: policyContainer
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      storageBlobDataReaderRoleDefinitionId
    )
    principalId: connectorNamespace.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output policyMcpServerUrl string = policyMcpServer.properties.mcpEndpointUrl
output dataverseMcpServerUrl string = dataverseMcpServer.properties.mcpEndpointUrl
output connectorNamespaceName string = connectorNamespace.name
output blobConnectionName string = blobConnection.name
output dataverseConnectionName string = dataverseConnection.name
output dataverseConnectionId string = dataverseConnection.id
output principalId string = connectorNamespace.identity.principalId
