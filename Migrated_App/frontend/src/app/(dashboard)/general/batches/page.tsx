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
  PlusIcon, 
  EyeIcon, 
  PencilIcon, 
  DocumentCheckIcon,
  XMarkIcon,
  ClockIcon,
  CalculatorIcon,
  PrinterIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface GLBatch {
  id: number
  batch_number: string
  batch_type: string
  batch_date: string
  description: string
  source_module: string
  total_debits: number
  total_credits: number
  entry_count: number
  is_balanced: boolean
  batch_status: string
  created_by: string
  created_date: string
  approved_by?: string
  approved_date?: string
  posted_by?: string
  posted_date?: string
  rejected_by?: string
  rejected_date?: string
  rejection_reason?: string
  period_number: number
  year_number: number
  notes?: string
}

// Schema
const batchSchema = z.object({
  batch_type: z.string().min(1, 'Batch type is required'),
  description: z.string().min(1, 'Description is required'),
  source_module: z.string().min(1, 'Source module is required'),
  notes: z.string().optional(),
})

// Mock data
const mockGLBatches: GLBatch[] = [
  {
    id: 1,
    batch_number: 'GL001234',
    batch_type: 'JOURNAL',
    batch_date: '2024-01-15',
    description: 'Monthly depreciation entries',
    source_module: 'GL',
    total_debits: 15000.00,
    total_credits: 15000.00,
    entry_count: 25,
    is_balanced: true,
    batch_status: 'POSTED',
    created_by: 'John Smith',
    created_date: '2024-01-15T09:00:00Z',
    approved_by: 'Manager',
    approved_date: '2024-01-15T14:30:00Z',
    posted_by: 'System',
    posted_date: '2024-01-15T15:00:00Z',
    period_number: 1,
    year_number: 2024,
    notes: 'Automated depreciation calculation',
  },
  {
    id: 2,
    batch_number: 'GL001235',
    batch_type: 'ACCRUAL',
    batch_date: '2024-01-16',
    description: 'Month-end accruals',
    source_module: 'GL',
    total_debits: 8500.00,
    total_credits: 8500.00,
    entry_count: 15,
    is_balanced: true,
    batch_status: 'APPROVED',
    created_by: 'Jane Doe',
    created_date: '2024-01-16T10:30:00Z',
    approved_by: 'Manager',
    approved_date: '2024-01-16T16:00:00Z',
    period_number: 1,
    year_number: 2024,
    notes: 'January accruals per management instructions',
  },
  {
    id: 3,
    batch_number: 'GL001236',
    batch_type: 'CORRECTION',
    batch_date: '2024-01-17',
    description: 'Correction of posting errors',
    source_module: 'GL',
    total_debits: 2500.00,
    total_credits: 2300.00,
    entry_count: 8,
    is_balanced: false,
    batch_status: 'PENDING',
    created_by: 'Bob Johnson',
    created_date: '2024-01-17T11:15:00Z',
    period_number: 1,
    year_number: 2024,
    notes: 'Needs review - out of balance',
  },
  {
    id: 4,
    batch_number: 'AP001100',
    batch_type: 'INVOICE',
    batch_date: '2024-01-18',
    description: 'Supplier invoice batch',
    source_module: 'AP',
    total_debits: 12500.00,
    total_credits: 12500.00,
    entry_count: 35,
    is_balanced: true,
    batch_status: 'REJECTED',
    created_by: 'Alice Wilson',
    created_date: '2024-01-18T08:45:00Z',
    rejected_by: 'Supervisor',
    rejected_date: '2024-01-18T14:20:00Z',
    rejection_reason: 'Missing supporting documentation',
    period_number: 1,
    year_number: 2024,
  },
  {
    id: 5,
    batch_number: 'AR001050',
    batch_type: 'INVOICE',
    batch_date: '2024-01-19',
    description: 'Customer invoice batch',
    source_module: 'AR',
    total_debits: 18750.00,
    total_credits: 18750.00,
    entry_count: 42,
    is_balanced: true,
    batch_status: 'PENDING',
    created_by: 'Charlie Brown',
    created_date: '2024-01-19T13:00:00Z',
    period_number: 1,
    year_number: 2024,
    notes: 'Ready for approval',
  },
]

const getBatchTypeBadge = (type: string) => {
  switch (type) {
    case 'JOURNAL':
      return <Badge variant="info">Journal</Badge>
    case 'ACCRUAL':
      return <Badge variant="warning">Accrual</Badge>
    case 'CORRECTION':
      return <Badge variant="danger">Correction</Badge>
    case 'INVOICE':
      return <Badge variant="success">Invoice</Badge>
    case 'PAYMENT':
      return <Badge variant="default">Payment</Badge>
    case 'ADJUSTMENT':
      return <Badge variant="default">Adjustment</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'DRAFT':
      return <Badge variant="default">Draft</Badge>
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'APPROVED':
      return <Badge variant="info">Approved</Badge>
    case 'POSTED':
      return <Badge variant="success">Posted</Badge>
    case 'REJECTED':
      return <Badge variant="danger">Rejected</Badge>
    case 'CANCELLED':
      return <Badge variant="default">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getSourceModuleBadge = (module: string) => {
  switch (module) {
    case 'GL':
      return <Badge variant="info" className="text-xs">GL</Badge>
    case 'AR':
      return <Badge variant="success" className="text-xs">AR</Badge>
    case 'AP':
      return <Badge variant="warning" className="text-xs">AP</Badge>
    case 'INV':
      return <Badge variant="default" className="text-xs">INV</Badge>
    default:
      return <Badge variant="default" className="text-xs">{module}</Badge>
  }
}

export default function GLBatchesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedBatch, setSelectedBatch] = useState<GLBatch | null>(null)

  const { data: glBatches, isLoading } = useQuery({
    queryKey: ['gl-batches'],
    queryFn: () => Promise.resolve(mockGLBatches),
  })

  const columns: ColumnDef<GLBatch>[] = [
    {
      accessorKey: 'batch_number',
      header: 'Batch Number',
    },
    {
      accessorKey: 'batch_date',
      header: 'Batch Date',
      cell: ({ row }) => {
        const date = row.getValue('batch_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'batch_type',
      header: 'Type',
      cell: ({ row }) => {
        return getBatchTypeBadge(row.getValue('batch_type'))
      },
    },
    {
      accessorKey: 'source_module',
      header: 'Module',
      cell: ({ row }) => {
        return getSourceModuleBadge(row.getValue('source_module'))
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
      accessorKey: 'entry_count',
      header: 'Entries',
      cell: ({ row }) => {
        const count = row.getValue('entry_count') as number
        return count.toLocaleString()
      },
    },
    {
      accessorKey: 'total_debits',
      header: 'Total Debits',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_debits'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'total_credits',
      header: 'Total Credits',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_credits'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      id: 'balance_check',
      header: 'Balanced',
      cell: ({ row }) => {
        const batch = row.original
        return batch.is_balanced ? (
          <Badge variant="success">Yes</Badge>
        ) : (
          <Badge variant="danger">No</Badge>
        )
      },
    },
    {
      accessorKey: 'batch_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('batch_status'))
      },
    },
    {
      accessorKey: 'period_number',
      header: 'Period',
      cell: ({ row }) => {
        const period = row.getValue('period_number') as number
        const year = row.original.year_number
        return `${period}/${year}`
      },
    },
    {
      accessorKey: 'created_by',
      header: 'Created By',
    },
    {
      accessorKey: 'created_date',
      header: 'Created Date',
      cell: ({ row }) => {
        const date = row.getValue('created_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const batch = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedBatch(batch)
                setShowEditModal(true)
              }}
              disabled={batch.batch_status === 'POSTED'}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view batch details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print batch
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {batch.batch_status === 'PENDING' && batch.is_balanced && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle approve batch
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {batch.batch_status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle post batch
                }}
              >
                <ArrowPathIcon className="h-4 w-4" />
              </Button>
            )}
            {(batch.batch_status === 'PENDING' || batch.batch_status === 'APPROVED') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle reject batch
                }}
              >
                <XMarkIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'batch_type',
      label: 'Batch Type',
      type: 'select',
      required: true,
      options: [
        { value: 'JOURNAL', label: 'Journal Entries' },
        { value: 'ACCRUAL', label: 'Accrual Entries' },
        { value: 'CORRECTION', label: 'Correction Entries' },
        { value: 'ADJUSTMENT', label: 'Adjustment Entries' },
        { value: 'RECLASSIFICATION', label: 'Reclassification' },
      ],
    },
    {
      name: 'description',
      label: 'Description',
      type: 'text',
      required: true,
    },
    {
      name: 'source_module',
      label: 'Source Module',
      type: 'select',
      required: true,
      options: [
        { value: 'GL', label: 'General Ledger (GL)' },
        { value: 'AR', label: 'Accounts Receivable (AR)' },
        { value: 'AP', label: 'Accounts Payable (AP)' },
        { value: 'INV', label: 'Inventory (INV)' },
        { value: 'FA', label: 'Fixed Assets (FA)' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateBatch = (data: any) => {
    console.log('Creating batch:', data)
    setShowCreateModal(false)
  }

  const handleEditBatch = (data: any) => {
    console.log('Editing batch:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="GL Batches"
        description="Manage general ledger batches and batch processing"
        breadcrumbs={[
          { label: 'General Ledger', href: '/general' },
          { label: 'GL Batches' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle batch trial balance
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Batch Trial Balance
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle pending batches
              }}
            >
              <ClockIcon className="h-4 w-4 mr-2" />
              Pending Batches
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Batch Posting Queue</h2>
                    <div style="background:#f3f4f6;padding:1rem;border-radius:4px;margin-bottom:1rem">
                      <p><strong>Batches in Queue:</strong> 5</p>
                      <p><strong>Processing:</strong> BATCH-2024-001</p>
                      <p><strong>Estimated Time:</strong> 2 minutes</p>
                    </div>
                    <div style="margin-bottom:1rem">
                      <h3 style="font-weight:bold;margin-bottom:0.5rem">Queue Status:</h3>
                      <div style="background:#fef3c7;padding:0.5rem;border-radius:4px;margin-bottom:0.25rem">BATCH-2024-001 - Processing...</div>
                      <div style="background:#dbeafe;padding:0.5rem;border-radius:4px;margin-bottom:0.25rem">BATCH-2024-002 - Queued</div>
                      <div style="background:#dbeafe;padding:0.5rem;border-radius:4px;margin-bottom:0.25rem">BATCH-2024-003 - Queued</div>
                      <div style="background:#dbeafe;padding:0.5rem;border-radius:4px;margin-bottom:0.25rem">BATCH-2024-004 - Queued</div>
                      <div style="background:#dbeafe;padding:0.5rem;border-radius:4px">BATCH-2024-005 - Queued</div>
                    </div>
                    <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              Posting Queue
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Batch
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={glBatches || []}
        searchPlaceholder="Search batches..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create GL Batch"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Batch Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>All entries in batch must be for the same period</li>
              <li>Batch must be balanced before approval</li>
              <li>Include clear description and notes</li>
              <li>Review entries before submitting for approval</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreateBatch}
            onCancel={() => setShowCreateModal(false)}
            schema={batchSchema}
            submitLabel="Create Batch"
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit GL Batch"
        size="lg"
      >
        {selectedBatch && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditBatch}
            onCancel={() => setShowEditModal(false)}
            schema={batchSchema}
            submitLabel="Update Batch"
            defaultValues={{
              batch_type: selectedBatch.batch_type,
              description: selectedBatch.description,
              source_module: selectedBatch.source_module,
              notes: selectedBatch.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}