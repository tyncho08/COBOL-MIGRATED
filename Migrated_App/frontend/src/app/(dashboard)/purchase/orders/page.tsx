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
import { PlusIcon, EyeIcon, PencilIcon } from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface PurchaseOrder {
  id: number
  order_number: string
  supplier_code: string
  order_date: string
  order_status: string
  total_value: number
  delivery_date?: string
  notes?: string
}

// Schemas
const purchaseOrderSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier is required'),
  delivery_date: z.string().optional(),
  notes: z.string().optional(),
})

// Mock data - replace with real API calls
const mockPurchaseOrders: PurchaseOrder[] = [
  {
    id: 1,
    order_number: 'PO000001',
    supplier_code: 'SUP001',
    order_date: '2024-01-15',
    order_status: 'PENDING',
    total_value: 1250.00,
    delivery_date: '2024-01-25',
  },
  {
    id: 2,
    order_number: 'PO000002',
    supplier_code: 'SUP002',
    order_date: '2024-01-16',
    order_status: 'APPROVED',
    total_value: 850.00,
    delivery_date: '2024-01-26',
  },
]

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'PENDING':
      return 'warning'
    case 'APPROVED':
      return 'success'
    case 'CANCELLED':
      return 'danger'
    default:
      return 'default'
  }
}

export default function PurchaseOrdersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null)

  // Mock query - replace with real API
  const { data: orders, isLoading } = useQuery({
    queryKey: ['purchase-orders'],
    queryFn: () => Promise.resolve(mockPurchaseOrders),
  })

  const columns: ColumnDef<PurchaseOrder>[] = [
    {
      accessorKey: 'order_number',
      header: 'Order Number',
    },
    {
      accessorKey: 'supplier_code',
      header: 'Supplier',
    },
    {
      accessorKey: 'order_date',
      header: 'Order Date',
      cell: ({ row }) => {
        return new Date(row.getValue('order_date')).toLocaleDateString()
      },
    },
    {
      accessorKey: 'order_status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.getValue('order_status') as string
        return (
          <Badge variant={getStatusBadgeVariant(status)}>
            {status}
          </Badge>
        )
      },
    },
    {
      accessorKey: 'total_value',
      header: 'Total Value',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_value'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'delivery_date',
      header: 'Delivery Date',
      cell: ({ row }) => {
        const date = row.getValue('delivery_date') as string
        return date ? new Date(date).toLocaleDateString() : '-'
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const order = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedOrder(order)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'supplier_code',
      label: 'Supplier',
      type: 'select',
      required: true,
      options: [
        { value: 'SUP001', label: 'Supplier 001' },
        { value: 'SUP002', label: 'Supplier 002' },
        { value: 'SUP003', label: 'Supplier 003' },
      ],
    },
    {
      name: 'delivery_date',
      label: 'Delivery Date',
      type: 'date',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateOrder = (data: any) => {
    console.log('Creating order:', data)
    setShowCreateModal(false)
  }

  const handleEditOrder = (data: any) => {
    console.log('Editing order:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        description="Manage purchase orders and track supplier deliveries"
        breadcrumbs={[
          { label: 'Purchase Ledger', href: '/purchase' },
          { label: 'Purchase Orders' },
        ]}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Purchase Order
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={orders || []}
        searchPlaceholder="Search purchase orders..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Purchase Order"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateOrder}
          onCancel={() => setShowCreateModal(false)}
          schema={purchaseOrderSchema}
          submitLabel="Create Order"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Purchase Order"
        size="lg"
      >
        {selectedOrder && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditOrder}
            onCancel={() => setShowEditModal(false)}
            schema={purchaseOrderSchema}
            submitLabel="Update Order"
            defaultValues={{
              supplier_code: selectedOrder.supplier_code,
              delivery_date: selectedOrder.delivery_date,
              notes: selectedOrder.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}