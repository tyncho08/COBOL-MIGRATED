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
                // Handle view config details
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
              onClick={() => {
                // Handle export config
              }}
            >
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Export Config
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle backup config
              }}
            >
              <DatabaseIcon className="h-4 w-4 mr-2" />
              Backup Config
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle security settings
              }}
            >
              <ShieldCheckIcon className="h-4 w-4 mr-2" />
              Security Settings
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle user permissions
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