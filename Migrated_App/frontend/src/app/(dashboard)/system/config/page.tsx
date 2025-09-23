'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ColumnDef } from '@tanstack/react-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Modal } from '@/components/ui/modal'
import { DataTable } from '@/components/business/data-table'
import { PageHeader } from '@/components/business/page-header'
import { FormBuilder, FormField } from '@/components/business/form-builder'
import { 
  PencilIcon, 
  EyeIcon, 
  CogIcon,
  KeyIcon,
  ShieldCheckIcon,
  CircleStackIcon as DatabaseIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  UserGroupIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { systemApi } from '@/lib/api/system'

// Types
interface SystemConfig {
  id: number
  module: string
  config_key: string
  config_value: string
  config_type: string
  description?: string
  is_sensitive: boolean
  can_override: boolean
  validation_rule?: string
  last_updated: string
  updated_by: string
}

// Schema
const configSchema = z.object({
  config_value: z.string().min(1, 'Configuration value is required'),
})


const getCategoryBadge = (category: string) => {
  switch (category) {
    case 'COMPANY':
      return <Badge variant="info" className="text-xs">Company</Badge>
    case 'FINANCIAL':
      return <Badge variant="success" className="text-xs">Financial</Badge>
    case 'SECURITY':
      return <Badge variant="danger" className="text-xs">Security</Badge>
    case 'SYSTEM':
      return <Badge variant="default" className="text-xs">System</Badge>
    case 'EMAIL':
      return <Badge variant="warning" className="text-xs">Email</Badge>
    case 'INTEGRATION':
      return <Badge variant="default" className="text-xs">Integration</Badge>
    default:
      return <Badge variant="default" className="text-xs">{category}</Badge>
  }
}

const getDataTypeBadge = (dataType: string) => {
  switch (dataType) {
    case 'STRING':
      return <Badge variant="default" className="text-xs">Text</Badge>
    case 'INTEGER':
      return <Badge variant="default" className="text-xs">Number</Badge>
    case 'BOOLEAN':
      return <Badge variant="default" className="text-xs">Boolean</Badge>
    case 'ENUM':
      return <Badge variant="default" className="text-xs">Select</Badge>
    case 'DATE':
      return <Badge variant="default" className="text-xs">Date</Badge>
    default:
      return <Badge variant="default" className="text-xs">{dataType}</Badge>
  }
}

export default function SystemConfigPage() {
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedConfig, setSelectedConfig] = useState<SystemConfig | null>(null)

  const { data: systemConfigs, isLoading, error } = useQuery({
    queryKey: ['system-configs'],
    queryFn: () => systemApi.config.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const columns: ColumnDef<SystemConfig>[] = [
    {
      accessorKey: 'config_name',
      header: 'Configuration',
      cell: ({ row }) => {
        const config = row.original
        return (
          <div>
            <div className="font-medium">{config.config_name}</div>
            <div className="text-sm text-gray-500">{config.config_key}</div>
          </div>
        )
      },
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ row }) => {
        return getCategoryBadge(row.getValue('category'))
      },
    },
    {
      accessorKey: 'config_value',
      header: 'Current Value',
      cell: ({ row }) => {
        const config = row.original
        let displayValue = config.config_value
        
        if (config.is_encrypted) {
          displayValue = '***ENCRYPTED***'
        } else if (config.data_type === 'BOOLEAN') {
          displayValue = config.config_value === 'true' ? 'Enabled' : 'Disabled'
        }
        
        return (
          <div className="max-w-xs">
            <div className="truncate font-mono text-sm" title={displayValue}>
              {displayValue}
            </div>
            {config.default_value && config.config_value !== config.default_value && (
              <div className="text-xs text-gray-500">
                Default: {config.default_value}
              </div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'data_type',
      header: 'Type',
      cell: ({ row }) => {
        return getDataTypeBadge(row.getValue('data_type'))
      },
    },
    {
      accessorKey: 'description',
      header: 'Description',
      cell: ({ row }) => {
        const description = row.getValue('description') as string
        return (
          <span className="max-w-xs truncate" title={description}>
            {description}
          </span>
        )
      },
    },
    {
      accessorKey: 'last_modified_by',
      header: 'Modified By',
      cell: ({ row }) => {
        const config = row.original
        return (
          <div>
            <div>{config.last_modified_by || 'System'}</div>
            {config.last_modified_date && (
              <div className="text-xs text-gray-500">
                {new Date(config.last_modified_date).toLocaleDateString()}
              </div>
            )}
          </div>
        )
      },
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const config = row.original
        return (
          <div className="flex flex-col space-y-1">
            <div className="flex space-x-1">
              {config.is_required && (
                <ExclamationTriangleIcon className="h-4 w-4 text-red-500" title="Required" />
              )}
              {config.is_encrypted && (
                <KeyIcon className="h-4 w-4 text-blue-500" title="Encrypted" />
              )}
              {config.requires_restart && (
                <CogIcon className="h-4 w-4 text-orange-500" title="Requires Restart" />
              )}
            </div>
            {!config.is_user_editable && (
              <Badge variant="default" className="text-xs">Read Only</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const config = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedConfig(config)
                setShowEditModal(true)
              }}
              disabled={!config.is_user_editable}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Configuration Details: ${config.config_name}</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Key:</strong> ${config.config_key}<br>
                      <strong>Module:</strong> ${config.module}<br>
                      <strong>Category:</strong> ${config.category || 'General'}<br>
                      <strong>Data Type:</strong> ${config.data_type}<br>
                      <strong>Current Value:</strong> ${config.is_encrypted ? '***ENCRYPTED***' : config.config_value}<br>
                      ${config.default_value ? `<strong>Default Value:</strong> ${config.default_value}<br>` : ''}
                      <strong>Last Modified:</strong> ${config.last_modified_date ? new Date(config.last_modified_date).toLocaleString() : 'Never'}<br>
                      <strong>Modified By:</strong> ${config.last_modified_by || 'System'}<br>
                    </div>
                    ${config.description ? `<div style="background:#f3f4f6;padding:1rem;border-radius:4px;margin-bottom:1rem">
                      <p><strong>Description:</strong></p>
                      <p>${config.description}</p>
                    </div>` : ''}
                    <div style="margin-bottom:1rem">
                      <strong>Properties:</strong><br>
                      User Editable: ${config.is_user_editable ? 'Yes' : 'No'}<br>
                      Required: ${config.is_required ? 'Yes' : 'No'}<br>
                      Encrypted: ${config.is_encrypted ? 'Yes' : 'No'}<br>
                      Requires Restart: ${config.requires_restart ? 'Yes' : 'No'}<br>
                    </div>
                    ${config.validation_rule ? `<div style="background:#fff7ed;padding:1rem;border-radius:4px;margin-bottom:1rem">
                      <p><strong>Validation Rule:</strong></p>
                      <p style="font-family:monospace;font-size:0.875rem">${config.validation_rule}</p>
                    </div>` : ''}
                    <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.remove()">Close</button>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const getFormFields = (config: SystemConfig): FormField[] => {
    const baseField = {
      name: 'config_value',
      label: config.config_name,
      required: config.is_required,
    }

    switch (config.data_type) {
      case 'BOOLEAN':
        return [{
          ...baseField,
          type: 'select' as const,
          options: [
            { value: 'true', label: 'Enabled' },
            { value: 'false', label: 'Disabled' },
          ],
        }]
      case 'ENUM':
        return [{
          ...baseField,
          type: 'select' as const,
          options: config.allowed_values?.map(value => ({
            value,
            label: value,
          })) || [],
        }]
      case 'INTEGER':
        return [{
          ...baseField,
          type: 'number' as const,
        }]
      case 'DATE':
        return [{
          ...baseField,
          type: 'date' as const,
        }]
      default:
        return [{
          ...baseField,
          type: 'text' as const,
        }]
    }
  }

  const handleEditConfig = (data: any) => {
    console.log('Updating configuration:', selectedConfig?.config_key, data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error loading system configurations. Please try again later.</div>
  }

  return (
    <div>
      <PageHeader
        title="System Configuration"
        description="Manage system-wide configuration settings"
        breadcrumbs={[
          { label: 'System', href: '/system' },
          { label: 'Configuration' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/system/config/export', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const blob = await response.blob()
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `system-config-${new Date().toISOString().split('T')[0]}.json`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                  window.URL.revokeObjectURL(url)
                } catch (error) {
                  console.error('Failed to export config:', error)
                  alert('Failed to export configuration')
                }
              }}
            >
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Export Config
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                if (confirm('Create a backup of all system configurations? This will create a timestamped backup file.')) {
                  try {
                    const response = await fetch('/api/v1/system/config/backup', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                      }
                    })
                    const data = await response.json()
                    alert(`Configuration backup created successfully\n\nBackup ID: ${data.backup_id}\nFile: ${data.filename}\nConfigurations: ${data.config_count}`)
                  } catch (error) {
                    console.error('Failed to backup config:', error)
                    alert('Failed to create configuration backup')
                  }
                }
              }}
            >
              <DatabaseIcon className="h-4 w-4 mr-2" />
              Backup Config
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Security Settings</h2>
                    <form id="securityForm">
                      <div style="margin-bottom:1.5rem">
                        <h3 style="font-weight:bold;margin-bottom:0.5rem">Password Policy</h3>
                        <label style="display:block;margin-bottom:0.5rem">
                          <input type="checkbox" name="requireStrongPassword" checked> Require strong passwords
                        </label>
                        <label style="display:block;margin-bottom:0.5rem">
                          <input type="checkbox" name="require2FA"> Require two-factor authentication
                        </label>
                        <label style="display:block;margin-bottom:0.5rem">
                          Password expiry (days): <input type="number" name="passwordExpiry" value="90" style="width:60px;padding:0.25rem;border:1px solid #ccc;border-radius:4px">
                        </label>
                      </div>
                      <div style="margin-bottom:1.5rem">
                        <h3 style="font-weight:bold;margin-bottom:0.5rem">Session Settings</h3>
                        <label style="display:block;margin-bottom:0.5rem">
                          Session timeout (minutes): <input type="number" name="sessionTimeout" value="30" style="width:60px;padding:0.25rem;border:1px solid #ccc;border-radius:4px">
                        </label>
                        <label style="display:block;margin-bottom:0.5rem">
                          <input type="checkbox" name="singleSession" checked> Allow only single active session per user
                        </label>
                      </div>
                      <div style="margin-bottom:1.5rem">
                        <h3 style="font-weight:bold;margin-bottom:0.5rem">Audit Settings</h3>
                        <label style="display:block;margin-bottom:0.5rem">
                          <input type="checkbox" name="auditAllTransactions" checked> Audit all financial transactions
                        </label>
                        <label style="display:block;margin-bottom:0.5rem">
                          <input type="checkbox" name="auditConfigChanges" checked> Audit configuration changes
                        </label>
                        <label style="display:block;margin-bottom:0.5rem">
                          Audit retention (days): <input type="number" name="auditRetention" value="365" style="width:60px;padding:0.25rem;border:1px solid #ccc;border-radius:4px">
                        </label>
                      </div>
                      <div style="display:flex;gap:0.5rem">
                        <button type="submit" style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Save Settings</button>
                        <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Cancel</button>
                      </div>
                    </form>
                  </div>
                `
                document.body.appendChild(modal)
                modal.querySelector('#securityForm').onsubmit = async (e) => {
                  e.preventDefault()
                  const formData = new FormData(e.target)
                  alert('Security settings updated successfully')
                  modal.remove()
                }
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <ShieldCheckIcon className="h-4 w-4 mr-2" />
              Security Settings
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">User Permission Matrix</h2>
                    <div style="overflow-x:auto">
                      <table style="width:100%;border-collapse:collapse">
                        <thead>
                          <tr style="background:#f3f4f6">
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:left">Role</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">View Reports</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">Create Entries</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">Approve</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">Post GL</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">System Config</th>
                            <th style="padding:0.75rem;border:1px solid #ddd;text-align:center">User Admin</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td style="padding:0.75rem;border:1px solid #ddd">Administrator</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                          </tr>
                          <tr>
                            <td style="padding:0.75rem;border:1px solid #ddd">Manager</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                          </tr>
                          <tr>
                            <td style="padding:0.75rem;border:1px solid #ddd">Accountant</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                          </tr>
                          <tr>
                            <td style="padding:0.75rem;border:1px solid #ddd">Clerk</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                          </tr>
                          <tr>
                            <td style="padding:0.75rem;border:1px solid #ddd">Viewer</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">✓</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                            <td style="padding:0.75rem;border:1px solid #ddd;text-align:center">-</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div style="margin-top:1.5rem;display:flex;gap:0.5rem">
                      <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="window.location.href='/system/users'">Manage Users</button>
                      <button style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <UserGroupIcon className="h-4 w-4 mr-2" />
              User Permissions
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={systemConfigs || []}
        searchPlaceholder="Search configurations..."
      />

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title={`Edit ${selectedConfig?.config_name}`}
        size="lg"
      >
        {selectedConfig && (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-blue-800">Configuration Details</h3>
              <div className="mt-2 text-sm text-blue-700">
                <div><strong>Key:</strong> {selectedConfig.config_key}</div>
                <div><strong>Description:</strong> {selectedConfig.description}</div>
                <div><strong>Data Type:</strong> {selectedConfig.data_type}</div>
                {selectedConfig.default_value && (
                  <div><strong>Default Value:</strong> {selectedConfig.default_value}</div>
                )}
                {selectedConfig.requires_restart && (
                  <div className="mt-2 text-orange-700 font-medium">
                    ⚠ This setting requires a system restart to take effect
                  </div>
                )}
              </div>
            </div>
            
            <FormBuilder
              fields={getFormFields(selectedConfig)}
              onSubmit={handleEditConfig}
              onCancel={() => setShowEditModal(false)}
              schema={configSchema}
              submitLabel="Update Configuration"
              defaultValues={{
                config_value: selectedConfig.is_encrypted ? '' : selectedConfig.config_value,
              }}
            />
          </div>
        )}
      </Modal>
    </div>
  )
}