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
  EyeIcon, 
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  UserIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { systemApi } from '@/lib/api/system'
import toast from 'react-hot-toast'

// Types
interface AuditTrail {
  id: number
  timestamp: string
  user_id: string
  user_name: string
  session_id: string
  action_type: string
  module: string
  table_name?: string
  record_id?: string
  action_description: string
  old_values?: string
  new_values?: string
  ip_address: string
  user_agent?: string
  result: string
  error_message?: string
  severity: string
  transaction_id?: string
  reference_number?: string
}

// Schema
const auditSearchSchema = z.object({
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  user_id: z.string().optional(),
  module: z.string().optional(),
  action_type: z.string().optional(),
  severity: z.string().optional(),
  result: z.string().optional(),
})


const getActionTypeBadge = (actionType: string) => {
  switch (actionType) {
    case 'CREATE':
      return <Badge variant="success">Create</Badge>
    case 'UPDATE':
      return <Badge variant="info">Update</Badge>
    case 'DELETE':
      return <Badge variant="danger">Delete</Badge>
    case 'LOGIN':
      return <Badge variant="default">Login</Badge>
    case 'LOGOUT':
      return <Badge variant="default">Logout</Badge>
    case 'EXPORT':
      return <Badge variant="warning">Export</Badge>
    case 'POST':
      return <Badge variant="info">Post</Badge>
    case 'BACKUP':
      return <Badge variant="default">Backup</Badge>
    default:
      return <Badge variant="default">{actionType}</Badge>
  }
}

const getResultBadge = (result: string) => {
  switch (result) {
    case 'SUCCESS':
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    case 'FAILURE':
      return <XCircleIcon className="h-5 w-5 text-red-500" />
    case 'WARNING':
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
    default:
      return <InformationCircleIcon className="h-5 w-5 text-blue-500" />
  }
}

const getSeverityBadge = (severity: string) => {
  switch (severity) {
    case 'ERROR':
      return <Badge variant="danger">Error</Badge>
    case 'WARNING':
      return <Badge variant="warning">Warning</Badge>
    case 'INFO':
      return <Badge variant="info">Info</Badge>
    case 'DEBUG':
      return <Badge variant="default">Debug</Badge>
    default:
      return <Badge variant="default">{severity}</Badge>
  }
}

export default function AuditTrailPage() {
  const [showSearchModal, setShowSearchModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedEntry, setSelectedEntry] = useState<AuditTrail | null>(null)
  const [searchParams, setSearchParams] = useState<any>({})

  const { data: auditTrail, isLoading, error, refetch } = useQuery({
    queryKey: ['audit-trail', searchParams],
    queryFn: () => systemApi.audit.getAll(searchParams),
    staleTime: 30000, // 30 seconds
  })

  const columns: ColumnDef<AuditTrail>[] = [
    {
      accessorKey: 'timestamp',
      header: 'Timestamp',
      cell: ({ row }) => {
        const timestamp = row.getValue('timestamp') as string
        const date = new Date(timestamp)
        return (
          <div>
            <div className="text-sm font-medium">
              {date.toLocaleDateString()}
            </div>
            <div className="text-xs text-gray-500">
              {date.toLocaleTimeString()}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'user_name',
      header: 'User',
      cell: ({ row }) => {
        const entry = row.original
        return (
          <div>
            <div className="font-medium">{entry.user_name}</div>
            <div className="text-xs text-gray-500">{entry.user_id}</div>
          </div>
        )
      },
    },
    {
      accessorKey: 'action_type',
      header: 'Action',
      cell: ({ row }) => {
        return getActionTypeBadge(row.getValue('action_type'))
      },
    },
    {
      accessorKey: 'module',
      header: 'Module',
    },
    {
      accessorKey: 'action_description',
      header: 'Description',
      cell: ({ row }) => {
        const description = row.getValue('action_description') as string
        const entry = row.original
        return (
          <div>
            <div className="max-w-xs truncate" title={description}>
              {description}
            </div>
            {entry.table_name && (
              <div className="text-xs text-gray-500">
                Table: {entry.table_name}
                {entry.record_id && ` (ID: ${entry.record_id})`}
              </div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'ip_address',
      header: 'IP Address',
      cell: ({ row }) => {
        return <span className="font-mono text-sm">{row.getValue('ip_address')}</span>
      },
    },
    {
      accessorKey: 'result',
      header: 'Result',
      cell: ({ row }) => {
        return getResultBadge(row.getValue('result'))
      },
    },
    {
      accessorKey: 'severity',
      header: 'Severity',
      cell: ({ row }) => {
        return getSeverityBadge(row.getValue('severity'))
      },
    },
    {
      id: 'ids',
      header: 'IDs',
      cell: ({ row }) => {
        const entry = row.original
        return (
          <div className="text-xs space-y-1">
            {entry.session_id && (
              <div title="Session ID">
                S: {entry.session_id.slice(-6)}
              </div>
            )}
            {entry.transaction_id && (
              <div title="Transaction ID">
                T: {entry.transaction_id.slice(-6)}
              </div>
            )}
            {entry.reference_number && (
              <div title="Reference Number">
                R: {entry.reference_number.slice(-6)}
              </div>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const entry = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedEntry(entry)
                setShowDetailModal(true)
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const searchFields: FormField[] = [
    {
      name: 'date_from',
      label: 'Date From',
      type: 'date',
    },
    {
      name: 'date_to',
      label: 'Date To',
      type: 'date',
    },
    {
      name: 'user_id',
      label: 'User ID',
      type: 'text',
    },
    {
      name: 'module',
      label: 'Module',
      type: 'select',
      options: [
        { value: '', label: 'All Modules' },
        { value: 'AUTHENTICATION', label: 'Authentication' },
        { value: 'CUSTOMERS', label: 'Customers' },
        { value: 'SUPPLIERS', label: 'Suppliers' },
        { value: 'GL', label: 'General Ledger' },
        { value: 'AR', label: 'Accounts Receivable' },
        { value: 'AP', label: 'Accounts Payable' },
        { value: 'INVENTORY', label: 'Inventory' },
        { value: 'REPORTS', label: 'Reports' },
        { value: 'USERS', label: 'User Management' },
        { value: 'SYSTEM', label: 'System' },
      ],
    },
    {
      name: 'action_type',
      label: 'Action Type',
      type: 'select',
      options: [
        { value: '', label: 'All Actions' },
        { value: 'CREATE', label: 'Create' },
        { value: 'UPDATE', label: 'Update' },
        { value: 'DELETE', label: 'Delete' },
        { value: 'LOGIN', label: 'Login' },
        { value: 'LOGOUT', label: 'Logout' },
        { value: 'EXPORT', label: 'Export' },
        { value: 'POST', label: 'Post' },
        { value: 'BACKUP', label: 'Backup' },
      ],
    },
    {
      name: 'severity',
      label: 'Severity',
      type: 'select',
      options: [
        { value: '', label: 'All Severities' },
        { value: 'ERROR', label: 'Error' },
        { value: 'WARNING', label: 'Warning' },
        { value: 'INFO', label: 'Info' },
        { value: 'DEBUG', label: 'Debug' },
      ],
    },
    {
      name: 'result',
      label: 'Result',
      type: 'select',
      options: [
        { value: '', label: 'All Results' },
        { value: 'SUCCESS', label: 'Success' },
        { value: 'FAILURE', label: 'Failure' },
        { value: 'WARNING', label: 'Warning' },
      ],
    },
  ]

  const handleSearch = (data: any) => {
    // Convert form data to API parameters
    const params: any = {}
    
    if (data.date_from) params.date_from = data.date_from
    if (data.date_to) params.date_to = data.date_to
    if (data.user_id) params.user = data.user_id
    if (data.module) params.module = data.module
    if (data.action_type) params.event_type = data.action_type
    if (data.severity) params.severity = data.severity
    if (data.result) params.result = data.result
    
    setSearchParams(params)
    setShowSearchModal(false)
    toast.success('Search filters applied')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading audit trail...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load audit trail</p>
          <Button onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Audit Trail"
        description="View and search system audit logs and user activities"
        breadcrumbs={[
          { label: 'System', href: '/system' },
          { label: 'Audit Trail' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => setShowSearchModal(true)}
            >
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Advanced Search
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await systemApi.audit.export('csv', searchParams)
                  toast.success('Audit log exported successfully')
                } catch (error) {
                  toast.error('Failed to export audit log')
                }
              }}
            >
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Export Log
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/system/audit/security-report', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Security Report</title></head>
                        <body>
                          <h1>Security Report</h1>
                          <h2>Failed Login Attempts</h2>
                          <p>Total: ${data.failed_logins}</p>
                          <h2>Suspicious Activities</h2>
                          <p>Total: ${data.suspicious_activities}</p>
                          <h2>High Risk Operations</h2>
                          <p>Total: ${data.high_risk_operations}</p>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  alert('Failed to generate security report')
                }
              }}
            >
              <ShieldCheckIcon className="h-4 w-4 mr-2" />
              Security Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/system/audit/user-activity', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>User Activity Report</title></head>
                        <body>
                          <h1>User Activity Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>User</th><th>Last Login</th><th>Total Actions</th><th>Failed Attempts</th></tr>
                            ${data.user_activities?.map((user: any) => 
                              `<tr><td>${user.user_name}</td><td>${user.last_login}</td><td>${user.total_actions}</td><td>${user.failed_attempts}</td></tr>`
                            ).join('')}
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  alert('Failed to generate user activity report')
                }
              }}
            >
              <UserIcon className="h-4 w-4 mr-2" />
              User Activity
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={auditTrail || []}
        searchPlaceholder="Search audit trail..."
      />

      {/* Advanced Search Modal */}
      <Modal
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
        title="Advanced Audit Search"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Search Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Leave fields empty to include all values</li>
              <li>Date range is inclusive of both start and end dates</li>
              <li>Results are limited to 1000 records maximum</li>
              <li>Large searches may take several seconds to complete</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={searchFields}
            onSubmit={handleSearch}
            onCancel={() => setShowSearchModal(false)}
            schema={auditSearchSchema}
            submitLabel="Search Audit Trail"
          />
        </div>
      </Modal>

      {/* Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Audit Trail Detail"
        size="xl"
      >
        {selectedEntry && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-700">Basic Information</h3>
                <div className="mt-2 space-y-2 text-sm">
                  <div><strong>Timestamp:</strong> {new Date(selectedEntry.timestamp).toLocaleString()}</div>
                  <div><strong>User:</strong> {selectedEntry.user_name} ({selectedEntry.user_id})</div>
                  <div><strong>Action:</strong> {selectedEntry.action_type}</div>
                  <div><strong>Module:</strong> {selectedEntry.module}</div>
                  <div><strong>Result:</strong> {selectedEntry.result}</div>
                  <div><strong>Severity:</strong> {selectedEntry.severity}</div>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-700">Technical Details</h3>
                <div className="mt-2 space-y-2 text-sm">
                  <div><strong>IP Address:</strong> {selectedEntry.ip_address}</div>
                  <div><strong>Session ID:</strong> {selectedEntry.session_id}</div>
                  {selectedEntry.transaction_id && (
                    <div><strong>Transaction ID:</strong> {selectedEntry.transaction_id}</div>
                  )}
                  {selectedEntry.reference_number && (
                    <div><strong>Reference:</strong> {selectedEntry.reference_number}</div>
                  )}
                  {selectedEntry.table_name && (
                    <div><strong>Table:</strong> {selectedEntry.table_name}</div>
                  )}
                  {selectedEntry.record_id && (
                    <div><strong>Record ID:</strong> {selectedEntry.record_id}</div>
                  )}
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-700">Description</h3>
              <p className="mt-2 text-sm text-gray-600">{selectedEntry.action_description}</p>
            </div>
            
            {selectedEntry.error_message && (
              <div>
                <h3 className="text-sm font-medium text-red-700">Error Message</h3>
                <p className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                  {selectedEntry.error_message}
                </p>
              </div>
            )}
            
            {selectedEntry.old_values && (
              <div>
                <h3 className="text-sm font-medium text-gray-700">Old Values</h3>
                <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                  {JSON.stringify(JSON.parse(selectedEntry.old_values), null, 2)}
                </pre>
              </div>
            )}
            
            {selectedEntry.new_values && (
              <div>
                <h3 className="text-sm font-medium text-gray-700">New Values</h3>
                <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                  {JSON.stringify(JSON.parse(selectedEntry.new_values), null, 2)}
                </pre>
              </div>
            )}
            
            {selectedEntry.user_agent && (
              <div>
                <h3 className="text-sm font-medium text-gray-700">User Agent</h3>
                <p className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {selectedEntry.user_agent}
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}