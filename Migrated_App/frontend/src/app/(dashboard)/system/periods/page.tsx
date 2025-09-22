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
  LockClosedIcon,
  LockOpenIcon,
  ArchiveBoxIcon,
  CalendarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface Period {
  id: number
  period_number: number
  period_name: string
  year_number: number
  start_date: string
  end_date: string
  period_type: string
  status: string
  is_current: boolean
  posting_allowed: boolean
  closed_by?: string
  closed_date?: string
  locked_by?: string
  locked_date?: string
  last_posting_date?: string
  transaction_count: number
  total_debits: number
  total_credits: number
  module_status: {
    gl: string
    ar: string
    ap: string
    inv: string
  }
  notes?: string
}

// Schema
const periodSchema = z.object({
  period_name: z.string().min(1, 'Period name is required'),
  period_number: z.string().min(1, 'Period number is required'),
  year_number: z.string().min(1, 'Year is required'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  period_type: z.string().min(1, 'Period type is required'),
  notes: z.string().optional(),
})

// Mock data
const mockPeriods: Period[] = [
  {
    id: 1,
    period_number: 1,
    period_name: 'January 2024',
    year_number: 2024,
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    period_type: 'REGULAR',
    status: 'CLOSED',
    is_current: false,
    posting_allowed: false,
    closed_by: 'System Admin',
    closed_date: '2024-02-05T17:00:00Z',
    locked_by: 'CFO',
    locked_date: '2024-02-10T09:00:00Z',
    last_posting_date: '2024-02-04T23:59:59Z',
    transaction_count: 1250,
    total_debits: 875000.00,
    total_credits: 875000.00,
    module_status: {
      gl: 'CLOSED',
      ar: 'CLOSED',
      ap: 'CLOSED',
      inv: 'CLOSED',
    },
    notes: 'Month-end close completed successfully',
  },
  {
    id: 2,
    period_number: 2,
    period_name: 'February 2024',
    year_number: 2024,
    start_date: '2024-02-01',
    end_date: '2024-02-29',
    period_type: 'REGULAR',
    status: 'OPEN',
    is_current: true,
    posting_allowed: true,
    last_posting_date: '2024-02-15T14:30:00Z',
    transaction_count: 856,
    total_debits: 650000.00,
    total_credits: 650000.00,
    module_status: {
      gl: 'OPEN',
      ar: 'OPEN',
      ap: 'OPEN',
      inv: 'OPEN',
    },
    notes: 'Current active period',
  },
  {
    id: 3,
    period_number: 3,
    period_name: 'March 2024',
    year_number: 2024,
    start_date: '2024-03-01',
    end_date: '2024-03-31',
    period_type: 'REGULAR',
    status: 'FUTURE',
    is_current: false,
    posting_allowed: false,
    transaction_count: 0,
    total_debits: 0.00,
    total_credits: 0.00,
    module_status: {
      gl: 'FUTURE',
      ar: 'FUTURE',
      ap: 'FUTURE',
      inv: 'FUTURE',
    },
    notes: 'Future period - not yet active',
  },
  {
    id: 13,
    period_number: 13,
    period_name: 'Year End Adjustments 2024',
    year_number: 2024,
    start_date: '2024-12-31',
    end_date: '2024-12-31',
    period_type: 'ADJUSTMENT',
    status: 'FUTURE',
    is_current: false,
    posting_allowed: false,
    transaction_count: 0,
    total_debits: 0.00,
    total_credits: 0.00,
    module_status: {
      gl: 'FUTURE',
      ar: 'CLOSED',
      ap: 'CLOSED',
      inv: 'CLOSED',
    },
    notes: 'Year-end adjustment period',
  },
  {
    id: 14,
    period_number: 12,
    period_name: 'December 2023',
    year_number: 2023,
    start_date: '2023-12-01',
    end_date: '2023-12-31',
    period_type: 'REGULAR',
    status: 'ARCHIVED',
    is_current: false,
    posting_allowed: false,
    closed_by: 'System Admin',
    closed_date: '2024-01-15T17:00:00Z',
    locked_by: 'CFO',
    locked_date: '2024-01-20T09:00:00Z',
    last_posting_date: '2024-01-10T23:59:59Z',
    transaction_count: 1485,
    total_debits: 1250000.00,
    total_credits: 1250000.00,
    module_status: {
      gl: 'ARCHIVED',
      ar: 'ARCHIVED',
      ap: 'ARCHIVED',
      inv: 'ARCHIVED',
    },
    notes: 'Prior year period - archived',
  },
]

const getPeriodTypeBadge = (type: string) => {
  switch (type) {
    case 'REGULAR':
      return <Badge variant="info">Regular</Badge>
    case 'ADJUSTMENT':
      return <Badge variant="warning">Adjustment</Badge>
    case 'YEAR_END':
      return <Badge variant="default">Year End</Badge>
    case 'OPENING':
      return <Badge variant="success">Opening</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (status: string, isCurrent: boolean) => {
  if (isCurrent) {
    return <Badge variant="success">Current</Badge>
  }
  
  switch (status) {
    case 'OPEN':
      return <Badge variant="info">Open</Badge>
    case 'CLOSED':
      return <Badge variant="warning">Closed</Badge>
    case 'LOCKED':
      return <Badge variant="default">Locked</Badge>
    case 'ARCHIVED':
      return <Badge variant="default">Archived</Badge>
    case 'FUTURE':
      return <Badge variant="default">Future</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getModuleStatusBadge = (status: string) => {
  switch (status) {
    case 'OPEN':
      return <Badge variant="success" className="text-xs">OPEN</Badge>
    case 'CLOSED':
      return <Badge variant="warning" className="text-xs">CLOSED</Badge>
    case 'LOCKED':
      return <Badge variant="default" className="text-xs">LOCKED</Badge>
    case 'ARCHIVED':
      return <Badge variant="default" className="text-xs">ARCH</Badge>
    case 'FUTURE':
      return <Badge variant="default" className="text-xs">FUT</Badge>
    default:
      return <Badge variant="default" className="text-xs">{status}</Badge>
  }
}

export default function PeriodsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState<Period | null>(null)

  const { data: periods, isLoading } = useQuery({
    queryKey: ['periods'],
    queryFn: () => Promise.resolve(mockPeriods),
  })

  const columns: ColumnDef<Period>[] = [
    {
      accessorKey: 'period_number',
      header: 'Period',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div>
            <div className="font-medium">
              {period.period_number}/{period.year_number}
            </div>
            <div className="text-sm text-gray-500">{period.period_name}</div>
          </div>
        )
      },
    },
    {
      accessorKey: 'period_type',
      header: 'Type',
      cell: ({ row }) => {
        return getPeriodTypeBadge(row.getValue('period_type'))
      },
    },
    {
      accessorKey: 'start_date',
      header: 'Start Date',
      cell: ({ row }) => {
        const date = row.getValue('start_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'end_date',
      header: 'End Date',
      cell: ({ row }) => {
        const date = row.getValue('end_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const period = row.original
        return getStatusBadge(row.getValue('status'), period.is_current)
      },
    },
    {
      accessorKey: 'transaction_count',
      header: 'Transactions',
      cell: ({ row }) => {
        const count = row.getValue('transaction_count') as number
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
        const period = row.original
        const isBalanced = Math.abs(period.total_debits - period.total_credits) < 0.01
        return isBalanced ? (
          <CheckCircleIcon className="h-5 w-5 text-green-500" />
        ) : (
          <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
        )
      },
    },
    {
      id: 'module_status',
      header: 'Module Status',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="grid grid-cols-2 gap-1">
            <div className="flex items-center space-x-1">
              <span className="text-xs">GL:</span>
              {getModuleStatusBadge(period.module_status.gl)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">AR:</span>
              {getModuleStatusBadge(period.module_status.ar)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">AP:</span>
              {getModuleStatusBadge(period.module_status.ap)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">INV:</span>
              {getModuleStatusBadge(period.module_status.inv)}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'closed_by',
      header: 'Closed By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="flex space-x-1">
            {period.is_current && (
              <Badge variant="success" className="text-xs">CURRENT</Badge>
            )}
            {period.posting_allowed && (
              <Badge variant="info" className="text-xs">POST</Badge>
            )}
            {period.locked_by && (
              <Badge variant="default" className="text-xs">LOCK</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedPeriod(period)
                setShowEditModal(true)
              }}
              disabled={period.status === 'ARCHIVED'}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view period details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            {period.status === 'OPEN' && !period.is_current && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle close period
                }}
              >
                <LockClosedIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'CLOSED' && !period.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle reopen period
                }}
              >
                <LockOpenIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'FUTURE' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle activate period
                }}
              >
                <CalendarIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'CLOSED' && period.year_number < new Date().getFullYear() && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle archive period
                }}
              >
                <ArchiveBoxIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'period_name',
      label: 'Period Name',
      type: 'text',
      required: true,
    },
    {
      name: 'period_number',
      label: 'Period Number',
      type: 'select',
      required: true,
      options: [
        { value: '1', label: 'Period 1' },
        { value: '2', label: 'Period 2' },
        { value: '3', label: 'Period 3' },
        { value: '4', label: 'Period 4' },
        { value: '5', label: 'Period 5' },
        { value: '6', label: 'Period 6' },
        { value: '7', label: 'Period 7' },
        { value: '8', label: 'Period 8' },
        { value: '9', label: 'Period 9' },
        { value: '10', label: 'Period 10' },
        { value: '11', label: 'Period 11' },
        { value: '12', label: 'Period 12' },
        { value: '13', label: 'Period 13 (Adjustments)' },
      ],
    },
    {
      name: 'year_number',
      label: 'Year',
      type: 'select',
      required: true,
      options: [
        { value: '2024', label: '2024' },
        { value: '2025', label: '2025' },
        { value: '2026', label: '2026' },
      ],
    },
    {
      name: 'start_date',
      label: 'Start Date',
      type: 'date',
      required: true,
    },
    {
      name: 'end_date',
      label: 'End Date',
      type: 'date',
      required: true,
    },
    {
      name: 'period_type',
      label: 'Period Type',
      type: 'select',
      required: true,
      options: [
        { value: 'REGULAR', label: 'Regular Period' },
        { value: 'ADJUSTMENT', label: 'Adjustment Period' },
        { value: 'YEAR_END', label: 'Year End Period' },
        { value: 'OPENING', label: 'Opening Period' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreatePeriod = (data: any) => {
    console.log('Creating period:', data)
    setShowCreateModal(false)
  }

  const handleEditPeriod = (data: any) => {
    console.log('Editing period:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Period Management"
        description="Manage accounting periods and period controls"
        breadcrumbs={[
          { label: 'System', href: '/system' },
          { label: 'Periods' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle period status report
              }}
            >
              <ClockIcon className="h-4 w-4 mr-2" />
              Period Status
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle month end checklist
              }}
            >
              <CheckCircleIcon className="h-4 w-4 mr-2" />
              Month End Checklist
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle year end procedures
              }}
            >
              <ArchiveBoxIcon className="h-4 w-4 mr-2" />
              Year End Procedures
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Period
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={periods || []}
        searchPlaceholder="Search periods..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Period"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">Period Creation Guidelines</h3>
            <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside">
              <li>Periods must be sequential and non-overlapping</li>
              <li>Start and end dates must be within the fiscal year</li>
              <li>Adjustment periods typically use the last day of fiscal year</li>
              <li>Only one period can be current at a time</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreatePeriod}
            onCancel={() => setShowCreateModal(false)}
            schema={periodSchema}
            submitLabel="Create Period"
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Period"
        size="lg"
      >
        {selectedPeriod && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditPeriod}
            onCancel={() => setShowEditModal(false)}
            schema={periodSchema}
            submitLabel="Update Period"
            defaultValues={{
              period_name: selectedPeriod.period_name,
              period_number: selectedPeriod.period_number.toString(),
              year_number: selectedPeriod.year_number.toString(),
              start_date: selectedPeriod.start_date,
              end_date: selectedPeriod.end_date,
              period_type: selectedPeriod.period_type,
              notes: selectedPeriod.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}