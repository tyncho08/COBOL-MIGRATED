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
  ClipboardDocumentCheckIcon,
  DocumentCheckIcon,
  PrinterIcon,
  CalculatorIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface StockTake {
  id: number
  take_number: string
  take_date: string
  take_status: string
  location: string
  take_type: string
  counted_by?: string
  checked_by?: string
  authorized_by?: string
  total_items: number
  items_counted: number
  items_pending: number
  variance_count: number
  variance_value: number
  adjustment_posted: boolean
  notes?: string
  created_at: string
  completed_at?: string
}

// Schema
const stockTakeSchema = z.object({
  location: z.string().min(1, 'Location is required'),
  take_type: z.string().min(1, 'Take type is required'),
  notes: z.string().optional(),
})

// Mock data
const mockStockTakes: StockTake[] = [
  {
    id: 1,
    take_number: 'ST001234',
    take_date: '2024-01-15',
    take_status: 'COMPLETED',
    location: 'WAREHOUSE-A',
    take_type: 'FULL',
    counted_by: 'John Smith',
    checked_by: 'Jane Doe',
    authorized_by: 'Manager',
    total_items: 150,
    items_counted: 150,
    items_pending: 0,
    variance_count: 5,
    variance_value: -125.50,
    adjustment_posted: true,
    notes: 'Annual stock take - all areas covered',
    created_at: '2024-01-15T09:00:00Z',
    completed_at: '2024-01-15T17:30:00Z',
  },
  {
    id: 2,
    take_number: 'ST001235',
    take_date: '2024-01-20',
    take_status: 'IN_PROGRESS',
    location: 'WAREHOUSE-B',
    take_type: 'PARTIAL',
    counted_by: 'Bob Johnson',
    total_items: 75,
    items_counted: 45,
    items_pending: 30,
    variance_count: 2,
    variance_value: 50.00,
    adjustment_posted: false,
    notes: 'Fast-moving items check',
    created_at: '2024-01-20T08:00:00Z',
  },
  {
    id: 3,
    take_number: 'ST001236',
    take_date: '2024-01-22',
    take_status: 'PLANNED',
    location: 'SHOP-FLOOR',
    take_type: 'CYCLE',
    total_items: 25,
    items_counted: 0,
    items_pending: 25,
    variance_count: 0,
    variance_value: 0.00,
    adjustment_posted: false,
    notes: 'Monthly cycle count - high value items',
    created_at: '2024-01-22T00:00:00Z',
  },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PLANNED':
      return <Badge variant="default">Planned</Badge>
    case 'IN_PROGRESS':
      return <Badge variant="warning">In Progress</Badge>
    case 'COMPLETED':
      return <Badge variant="info">Completed</Badge>
    case 'AUTHORIZED':
      return <Badge variant="success">Authorized</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getTakeTypeBadge = (type: string) => {
  switch (type) {
    case 'FULL':
      return <Badge variant="info">Full Count</Badge>
    case 'PARTIAL':
      return <Badge variant="warning">Partial Count</Badge>
    case 'CYCLE':
      return <Badge variant="default">Cycle Count</Badge>
    case 'SPOT':
      return <Badge variant="default">Spot Check</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

export default function StockTakesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedTake, setSelectedTake] = useState<StockTake | null>(null)

  const { data: stockTakes, isLoading } = useQuery({
    queryKey: ['stock-takes'],
    queryFn: () => Promise.resolve(mockStockTakes),
  })

  const columns: ColumnDef<StockTake>[] = [
    {
      accessorKey: 'take_number',
      header: 'Take Number',
    },
    {
      accessorKey: 'take_date',
      header: 'Take Date',
      cell: ({ row }) => {
        const date = row.getValue('take_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'take_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('take_status'))
      },
    },
    {
      accessorKey: 'location',
      header: 'Location',
    },
    {
      accessorKey: 'take_type',
      header: 'Type',
      cell: ({ row }) => {
        return getTakeTypeBadge(row.getValue('take_type'))
      },
    },
    {
      accessorKey: 'total_items',
      header: 'Total Items',
      cell: ({ row }) => {
        const total = row.getValue('total_items') as number
        return total.toLocaleString()
      },
    },
    {
      accessorKey: 'items_counted',
      header: 'Counted',
      cell: ({ row }) => {
        const counted = row.getValue('items_counted') as number
        const total = row.original.total_items
        const percentage = total > 0 ? (counted / total * 100).toFixed(1) : '0.0'
        return (
          <span className={counted < total ? 'text-orange-600' : 'text-green-600'}>
            {counted.toLocaleString()} ({percentage}%)
          </span>
        )
      },
    },
    {
      accessorKey: 'items_pending',
      header: 'Pending',
      cell: ({ row }) => {
        const pending = row.getValue('items_pending') as number
        return (
          <span className={pending > 0 ? 'text-red-600 font-semibold' : ''}>
            {pending.toLocaleString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'variance_count',
      header: 'Variances',
      cell: ({ row }) => {
        const variances = row.getValue('variance_count') as number
        return (
          <span className={variances > 0 ? 'text-orange-600 font-semibold' : 'text-green-600'}>
            {variances.toLocaleString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'variance_value',
      header: 'Variance Value',
      cell: ({ row }) => {
        const value = parseFloat(row.getValue('variance_value'))
        return (
          <span className={value !== 0 ? (value > 0 ? 'text-green-600' : 'text-red-600') : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(value)}
          </span>
        )
      },
    },
    {
      accessorKey: 'counted_by',
      header: 'Counted By',
    },
    {
      accessorKey: 'checked_by',
      header: 'Checked By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const take = row.original
        return (
          <div className="flex space-x-1">
            {take.adjustment_posted && (
              <Badge variant="success" className="text-xs">ADJ</Badge>
            )}
            {take.authorized_by && (
              <Badge variant="info" className="text-xs">AUTH</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const take = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedTake(take)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view take details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print counting sheets
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {take.take_status === 'COMPLETED' && !take.adjustment_posted && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle post adjustments
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {take.take_status === 'IN_PROGRESS' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle counting interface
                }}
              >
                <CalculatorIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      required: true,
      options: [
        { value: 'WAREHOUSE-A', label: 'Warehouse A' },
        { value: 'WAREHOUSE-B', label: 'Warehouse B' },
        { value: 'SHOP-FLOOR', label: 'Shop Floor' },
        { value: 'RETURNS', label: 'Returns Area' },
        { value: 'ALL', label: 'All Locations' },
      ],
    },
    {
      name: 'take_type',
      label: 'Take Type',
      type: 'select',
      required: true,
      options: [
        { value: 'FULL', label: 'Full Stock Take' },
        { value: 'PARTIAL', label: 'Partial Count' },
        { value: 'CYCLE', label: 'Cycle Count' },
        { value: 'SPOT', label: 'Spot Check' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateTake = (data: any) => {
    console.log('Creating stock take:', data)
    setShowCreateModal(false)
  }

  const handleEditTake = (data: any) => {
    console.log('Editing stock take:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Stock Takes"
        description="Manage stock counting and inventory verification"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Takes' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle variance report
              }}
            >
              Variance Report
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle counting sheets
              }}
            >
              <ClipboardDocumentCheckIcon className="h-4 w-4 mr-2" />
              Counting Sheets
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Stock Take
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={stockTakes || []}
        searchPlaceholder="Search stock takes..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Stock Take"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateTake}
          onCancel={() => setShowCreateModal(false)}
          schema={stockTakeSchema}
          submitLabel="Create Stock Take"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Stock Take"
        size="lg"
      >
        {selectedTake && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditTake}
            onCancel={() => setShowEditModal(false)}
            schema={stockTakeSchema}
            submitLabel="Update Stock Take"
            defaultValues={{
              location: selectedTake.location,
              take_type: selectedTake.take_type,
              notes: selectedTake.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}