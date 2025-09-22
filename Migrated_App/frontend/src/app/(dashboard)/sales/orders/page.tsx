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
import { PlusIcon, EyeIcon, PencilIcon, CheckIcon, XMarkIcon, PrinterIcon } from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface SalesOrder {
  id: number
  order_number: string
  order_date: string
  customer_id: number
  customer_code: string
  customer_name: string
  customer_reference?: string
  required_date?: string
  order_status: string
  gross_total: number
  vat_total: number
  net_total: number
  is_delivered: boolean
  is_invoiced: boolean
  sales_rep?: string
  notes?: string
}

// Schema
const salesOrderSchema = z.object({
  customer_code: z.string().min(1, 'Customer is required'),
  customer_reference: z.string().optional(),
  required_date: z.string().optional(),
  delivery_name: z.string().optional(),
  delivery_address1: z.string().optional(),
  delivery_address2: z.string().optional(),
  delivery_postcode: z.string().optional(),
  sales_rep: z.string().optional(),
  notes: z.string().optional(),
  order_lines: z.array(z.object({
    stock_code: z.string().min(1, 'Stock code is required'),
    description: z.string().min(1, 'Description is required'),
    quantity_ordered: z.string().min(1, 'Quantity is required'),
    unit_price: z.string().min(1, 'Unit price is required'),
    discount_percent: z.string().optional(),
  })).min(1, 'At least one order line is required'),
})

// Mock data
const mockSalesOrders: SalesOrder[] = [
  {
    id: 1,
    order_number: 'SO001234',
    order_date: '2024-01-15',
    customer_id: 1,
    customer_code: 'CUST001',
    customer_name: 'ABC Corporation',
    customer_reference: 'PO-2024-001',
    required_date: '2024-01-30',
    order_status: 'APPROVED',
    gross_total: 2500.00,
    vat_total: 500.00,
    net_total: 3000.00,
    is_delivered: false,
    is_invoiced: false,
    sales_rep: 'REP001',
    notes: 'Urgent delivery required',
  },
  {
    id: 2,
    order_number: 'SO001235',
    order_date: '2024-01-16',
    customer_id: 2,
    customer_code: 'CUST002',
    customer_name: 'XYZ Ltd',
    customer_reference: 'REQ-456',
    required_date: '2024-02-01',
    order_status: 'PENDING',
    gross_total: 1200.00,
    vat_total: 240.00,
    net_total: 1440.00,
    is_delivered: false,
    is_invoiced: false,
    sales_rep: 'REP002',
  },
  {
    id: 3,
    order_number: 'SO001236',
    order_date: '2024-01-17',
    customer_id: 3,
    customer_code: 'CUST003',
    customer_name: 'Tech Solutions Inc',
    required_date: '2024-01-25',
    order_status: 'DELIVERED',
    gross_total: 5000.00,
    vat_total: 1000.00,
    net_total: 6000.00,
    is_delivered: true,
    is_invoiced: true,
    sales_rep: 'REP001',
  },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'APPROVED':
      return <Badge variant="info">Approved</Badge>
    case 'DELIVERED':
      return <Badge variant="success">Delivered</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    case 'INVOICED':
      return <Badge variant="success">Invoiced</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function SalesOrdersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<SalesOrder | null>(null)

  const { data: salesOrders, isLoading } = useQuery({
    queryKey: ['sales-orders'],
    queryFn: () => Promise.resolve(mockSalesOrders),
  })

  const columns: ColumnDef<SalesOrder>[] = [
    {
      accessorKey: 'order_number',
      header: 'Order Number',
    },
    {
      accessorKey: 'order_date',
      header: 'Order Date',
      cell: ({ row }) => {
        const date = row.getValue('order_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'customer_code',
      header: 'Customer',
    },
    {
      accessorKey: 'customer_name',
      header: 'Customer Name',
    },
    {
      accessorKey: 'customer_reference',
      header: 'Cust. Ref.',
    },
    {
      accessorKey: 'required_date',
      header: 'Required Date',
      cell: ({ row }) => {
        const date = row.getValue('required_date') as string
        return date ? new Date(date).toLocaleDateString() : '-'
      },
    },
    {
      accessorKey: 'order_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('order_status'))
      },
    },
    {
      accessorKey: 'net_total',
      header: 'Total',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('net_total'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'sales_rep',
      header: 'Sales Rep',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const order = row.original
        return (
          <div className="flex space-x-1">
            {order.is_delivered && (
              <Badge variant="success" className="text-xs">D</Badge>
            )}
            {order.is_invoiced && (
              <Badge variant="info" className="text-xs">I</Badge>
            )}
          </div>
        )
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
                // Handle view order details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print order
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {order.order_status === 'PENDING' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle approve order
                }}
              >
                <CheckIcon className="h-4 w-4" />
              </Button>
            )}
            {order.order_status !== 'CANCELLED' && order.order_status !== 'INVOICED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle cancel order
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
      name: 'customer_code',
      label: 'Customer',
      type: 'select',
      required: true,
      options: [
        { value: 'CUST001', label: 'CUST001 - ABC Corporation' },
        { value: 'CUST002', label: 'CUST002 - XYZ Ltd' },
        { value: 'CUST003', label: 'CUST003 - Tech Solutions Inc' },
      ],
    },
    {
      name: 'customer_reference',
      label: 'Customer Reference',
      type: 'text',
    },
    {
      name: 'required_date',
      label: 'Required Date',
      type: 'date',
    },
    {
      name: 'delivery_name',
      label: 'Delivery Name',
      type: 'text',
    },
    {
      name: 'delivery_address1',
      label: 'Delivery Address Line 1',
      type: 'text',
    },
    {
      name: 'delivery_address2',
      label: 'Delivery Address Line 2',
      type: 'text',
    },
    {
      name: 'delivery_postcode',
      label: 'Delivery Postcode',
      type: 'text',
    },
    {
      name: 'sales_rep',
      label: 'Sales Representative',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'REP001', label: 'REP001 - John Smith' },
        { value: 'REP002', label: 'REP002 - Jane Doe' },
        { value: 'REP003', label: 'REP003 - Bob Johnson' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateOrder = (data: any) => {
    console.log('Creating sales order:', data)
    setShowCreateModal(false)
  }

  const handleEditOrder = (data: any) => {
    console.log('Editing sales order:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Sales Orders"
        description="Manage sales orders and track order fulfillment"
        breadcrumbs={[
          { label: 'Sales Ledger', href: '/sales' },
          { label: 'Sales Orders' },
        ]}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Sales Order
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={salesOrders || []}
        searchPlaceholder="Search sales orders..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Sales Order"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateOrder}
          onCancel={() => setShowCreateModal(false)}
          schema={salesOrderSchema}
          submitLabel="Create Order"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Sales Order"
        size="xl"
      >
        {selectedOrder && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditOrder}
            onCancel={() => setShowEditModal(false)}
            schema={salesOrderSchema}
            submitLabel="Update Order"
            defaultValues={{
              customer_code: selectedOrder.customer_code,
              customer_reference: selectedOrder.customer_reference,
              required_date: selectedOrder.required_date,
              sales_rep: selectedOrder.sales_rep,
              notes: selectedOrder.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}