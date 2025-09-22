'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ColumnDef } from '@tanstack/react-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Modal } from '@/components/ui/modal'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { DataTable } from '@/components/business/data-table'
import { PageHeader } from '@/components/business/page-header'
import { FormBuilder, FormField } from '@/components/business/form-builder'
import { 
  PlusIcon, 
  EyeIcon, 
  PencilIcon, 
  CheckCircleIcon,
  XCircleIcon,
  PrinterIcon,
  TrashIcon,
  TruckIcon,
  DocumentDuplicateIcon,
  ClipboardDocumentListIcon,
  EnvelopeIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { SalesOrder, SalesOrderLine, salesOrdersApi } from '@/lib/api/sales-orders'
import { customersApi } from '@/lib/api/customers'
import { stockItemsApi } from '@/lib/api/stock-items'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'


// Schema
const salesOrderSchema = z.object({
  customer_id: z.string().min(1, 'Customer is required'),
  delivery_date: z.string().optional(),
  reference: z.string().optional(),
  customer_order_no: z.string().optional(),
  delivery_address: z.string().optional(),
  sales_rep: z.string().optional(),
  payment_terms: z.string().optional(),
  currency_code: z.string().min(1, 'Currency is required'),
  notes: z.string().optional(),
})

// Order line schema
const orderLineSchema = z.object({
  stock_code: z.string().min(1, 'Stock item is required'),
  quantity: z.string().min(1, 'Quantity is required'),
  unit_price: z.string().min(1, 'Unit price is required'),
  discount_percent: z.string().optional(),
  vat_code: z.string().min(1, 'VAT code is required'),
  delivery_date: z.string().optional(),
  notes: z.string().optional(),
})

// Shipping schema
const shippingSchema = z.object({
  tracking_number: z.string().optional(),
  carrier: z.string().optional(),
  shipping_date: z.string().optional(),
})

// Email schema
const emailSchema = z.object({
  to: z.string().email('Valid email address is required'),
  subject: z.string().min(1, 'Subject is required'),
  message: z.string().optional(),
})


const getStatusBadge = (status: string) => {
  switch (status) {
    case 'DRAFT':
      return <Badge variant="default">Draft</Badge>
    case 'CONFIRMED':
      return <Badge variant="info">Confirmed</Badge>
    case 'PROCESSING':
      return <Badge variant="warning">Processing</Badge>
    case 'SHIPPED':
      return <Badge variant="info">Shipped</Badge>
    case 'DELIVERED':
      return <Badge variant="success">Delivered</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function SalesOrdersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showLinesModal, setShowLinesModal] = useState(false)
  const [showAddLineModal, setShowAddLineModal] = useState(false)
  const [showShippingModal, setShowShippingModal] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<SalesOrder | null>(null)
  const [orderToDelete, setOrderToDelete] = useState<SalesOrder | null>(null)
  
  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for sales orders
  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['salesOrders'],
    queryFn: () => salesOrdersApi.getAll(),
  })

  // Query for customers
  const { data: customers } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.getAll(),
  })

  // Query for stock items
  const { data: stockItems } = useQuery({
    queryKey: ['stockItems'],
    queryFn: () => stockItemsApi.getAll(),
  })

  // Query for order lines when viewing
  const { data: orderLines } = useQuery({
    queryKey: ['salesOrderLines', selectedOrder?.id],
    queryFn: () => selectedOrder?.id ? salesOrdersApi.getLines(selectedOrder.id) : null,
    enabled: !!selectedOrder?.id && showLinesModal,
  })

  // Mutation for creating sales order
  const createMutation = useMutation({
    mutationFn: salesOrdersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create sales order')
    },
  })

  // Mutation for updating sales order
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<SalesOrder> }) =>
      salesOrdersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update sales order')
    },
  })

  // Mutation for deleting sales order
  const deleteMutation = useMutation({
    mutationFn: salesOrdersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete sales order')
    },
  })

  // Mutation for approving order
  const approveMutation = useMutation({
    mutationFn: salesOrdersApi.approve,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order approved successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve sales order')
    },
  })

  // Mutation for cancelling order
  const cancelMutation = useMutation({
    mutationFn: salesOrdersApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order cancelled successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel sales order')
    },
  })

  // Mutation for adding order line
  const addLineMutation = useMutation({
    mutationFn: ({ orderId, line }: { orderId: number; line: Omit<SalesOrderLine, 'id'> }) =>
      salesOrdersApi.addLine(orderId, line),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      queryClient.invalidateQueries({ queryKey: ['salesOrderLines'] })
      toast.success('Line added successfully')
      setShowAddLineModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add line')
    },
  })

  // Mutation for shipping order
  const shipMutation = useMutation({
    mutationFn: ({ orderId, shipData }: { orderId: number; shipData?: any }) =>
      salesOrdersApi.ship(orderId, shipData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order shipped successfully')
      setShowShippingModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to ship sales order')
    },
  })

  // Mutation for converting to invoice
  const convertToInvoiceMutation = useMutation({
    mutationFn: salesOrdersApi.convertToInvoice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      toast.success('Sales order converted to invoice successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to convert to invoice')
    },
  })

  // Mutation for emailing order
  const emailMutation = useMutation({
    mutationFn: ({ orderId, emailData }: { orderId: number; emailData: any }) =>
      salesOrdersApi.email(orderId, emailData),
    onSuccess: () => {
      toast.success('Sales order emailed successfully')
      setShowEmailModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to email sales order')
    },
  })

  const columns: ColumnDef<SalesOrder>[] = [
    {
      accessorKey: 'order_number',
      header: 'Order Number',
    },
    {
      accessorKey: 'customer_code',
      header: 'Customer',
      cell: ({ row }) => {
        const order = row.original
        return (
          <div>
            <div className="font-medium">{order.customer_code}</div>
            {order.customer_name && (
              <div className="text-sm text-gray-500">{order.customer_name}</div>
            )}
          </div>
        )
      },
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
      accessorKey: 'delivery_date',
      header: 'Delivery Date',
      cell: ({ row }) => {
        const date = row.getValue('delivery_date') as string
        return date ? new Date(date).toLocaleDateString() : '-'
      },
    },
    {
      accessorKey: 'reference',
      header: 'Reference',
      cell: ({ row }) => row.getValue('reference') || '-',
    },
    {
      accessorKey: 'customer_order_no',
      header: 'Cust. Order No',
      cell: ({ row }) => row.getValue('customer_order_no') || '-',
    },
    {
      accessorKey: 'sub_total',
      header: 'Sub Total',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('sub_total') || '0')
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: row.original.currency_code || 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'vat_amount',
      header: 'VAT',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('vat_amount') || '0')
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: row.original.currency_code || 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'total_amount',
      header: 'Total',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_amount') || '0')
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: row.original.currency_code || 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('status'))
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const order = row.original
        const canConfirm = order.status === 'DRAFT' && canEdit('sales')
        const canCancel = ['DRAFT', 'CONFIRMED'].includes(order.status) && canEdit('sales')
        const canShip = order.status === 'CONFIRMED' && canEdit('sales')
        
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedOrder(order)
                setShowEditModal(true)
              }}
              title="Edit"
              disabled={!['DRAFT'].includes(order.status)}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedOrder(order)
                setShowLinesModal(true)
              }}
              title="View Lines"
            >
              <ClipboardDocumentListIcon className="h-4 w-4" />
            </Button>
            {canConfirm && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleApprove(order)}
                title="Confirm Order"
                className="text-green-600 hover:text-green-700"
              >
                <CheckCircleIcon className="h-4 w-4" />
              </Button>
            )}
            {canCancel && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleCancel(order)}
                title="Cancel Order"
                className="text-red-600 hover:text-red-700"
              >
                <XCircleIcon className="h-4 w-4" />
              </Button>
            )}
            {canShip && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedOrder(order)
                  setShowShippingModal(true)
                }}
                title="Ship Order"
              >
                <TruckIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await salesOrdersApi.print(order.id!)
                  toast.success('Order printed')
                } catch (error) {
                  toast.error('Failed to print order')
                }
              }}
              title="Print"
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedOrder(order)
                setShowEmailModal(true)
              }}
              title="Email Order"
            >
              <EnvelopeIcon className="h-4 w-4" />
            </Button>
            {order.status === 'CONFIRMED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleConvertToInvoice(order)}
                title="Convert to Invoice"
              >
                <DocumentDuplicateIcon className="h-4 w-4" />
              </Button>
            )}
            {canDelete('sales') && order.status === 'DRAFT' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteOrder(order)}
                className="text-red-600 hover:text-red-700"
                title="Delete"
              >
                <TrashIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'customer_id',
      label: 'Customer',
      type: 'select',
      required: true,
      options: Array.isArray(customers) 
        ? customers.map((c: any) => ({ 
            value: c.id!.toString(), 
            label: `${c.customer_code} - ${c.customer_name}` 
          }))
        : [],
    },
    {
      name: 'delivery_date',
      label: 'Delivery Date',
      type: 'date',
    },
    {
      name: 'reference',
      label: 'Our Reference',
      type: 'text',
    },
    {
      name: 'customer_order_no',
      label: 'Customer Order No',
      type: 'text',
    },
    {
      name: 'delivery_address',
      label: 'Delivery Address',
      type: 'textarea',
    },
    {
      name: 'sales_rep',
      label: 'Sales Representative',
      type: 'text',
    },
    {
      name: 'payment_terms',
      label: 'Payment Terms',
      type: 'select',
      options: [
        { value: '', label: 'Default' },
        { value: '7 DAYS', label: '7 Days' },
        { value: '14 DAYS', label: '14 Days' },
        { value: '30 DAYS', label: '30 Days' },
        { value: '60 DAYS', label: '60 Days' },
        { value: 'COD', label: 'Cash on Delivery' },
      ],
    },
    {
      name: 'currency_code',
      label: 'Currency',
      type: 'select',
      required: true,
      options: [
        { value: 'USD', label: 'US Dollar' },
        { value: 'EUR', label: 'Euro' },
        { value: 'GBP', label: 'British Pound' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const lineFormFields: FormField[] = [
    {
      name: 'stock_code',
      label: 'Stock Item',
      type: 'select',
      required: true,
      options: Array.isArray(stockItems)
        ? stockItems.map((item: any) => ({ 
            value: item.stock_code, 
            label: `${item.stock_code} - ${item.description}` 
          }))
        : [],
    },
    {
      name: 'quantity',
      label: 'Quantity',
      type: 'number',
      required: true,
    },
    {
      name: 'unit_price',
      label: 'Unit Price',
      type: 'number',
      required: true,
    },
    {
      name: 'discount_percent',
      label: 'Discount %',
      type: 'number',
    },
    {
      name: 'vat_code',
      label: 'VAT Code',
      type: 'select',
      required: true,
      options: [
        { value: 'S', label: 'Standard Rate (20%)' },
        { value: 'R', label: 'Reduced Rate (5%)' },
        { value: 'Z', label: 'Zero Rated (0%)' },
        { value: 'E', label: 'Exempt' },
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

  const shippingFormFields: FormField[] = [
    {
      name: 'tracking_number',
      label: 'Tracking Number',
      type: 'text',
    },
    {
      name: 'carrier',
      label: 'Carrier',
      type: 'select',
      options: [
        { value: '', label: 'Select Carrier' },
        { value: 'FedEx', label: 'FedEx' },
        { value: 'UPS', label: 'UPS' },
        { value: 'DHL', label: 'DHL' },
        { value: 'USPS', label: 'USPS' },
        { value: 'Other', label: 'Other' },
      ],
    },
    {
      name: 'shipping_date',
      label: 'Shipping Date',
      type: 'date',
    },
  ]

  const emailFormFields: FormField[] = [
    {
      name: 'to',
      label: 'To',
      type: 'email',
      required: true,
      placeholder: 'customer@example.com',
    },
    {
      name: 'subject',
      label: 'Subject',
      type: 'text',
      required: true,
      placeholder: 'Sales Order Confirmation',
    },
    {
      name: 'message',
      label: 'Message',
      type: 'textarea',
      placeholder: 'Please find your sales order attached...',
    },
  ]

  const handleCreateOrder = (data: any) => {
    const orderData = {
      ...data,
      customer_id: parseInt(data.customer_id),
      order_date: new Date().toISOString().split('T')[0],
      exchange_rate: 1,
      status: 'DRAFT' as const,
      order_lines: [],
      customer_code: customers?.find(c => c.id === parseInt(data.customer_id))?.customer_code || '',
    }
    createMutation.mutate(orderData)
  }

  const handleEditOrder = (data: any) => {
    if (selectedOrder?.id) {
      const orderData = {
        ...data,
        customer_id: parseInt(data.customer_id),
        customer_code: customers?.find(c => c.id === parseInt(data.customer_id))?.customer_code || '',
      }
      updateMutation.mutate({ id: selectedOrder.id, data: orderData })
    }
  }

  const handleDeleteOrder = (order: SalesOrder) => {
    setOrderToDelete(order)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (orderToDelete?.id) {
      deleteMutation.mutate(orderToDelete.id)
      setShowDeleteDialog(false)
      setOrderToDelete(null)
    }
  }

  const handleApprove = (order: SalesOrder) => {
    if (order.id) {
      approveMutation.mutate(order.id)
    }
  }

  const handleCancel = (order: SalesOrder) => {
    if (order.id) {
      cancelMutation.mutate(order.id)
    }
  }

  const handleAddLine = (data: any) => {
    if (selectedOrder?.id) {
      const lineData = {
        line_number: (orderLines?.length || 0) + 1,
        stock_code: data.stock_code,
        description: stockItems?.find(i => i.stock_code === data.stock_code)?.description || '',
        quantity: parseFloat(data.quantity),
        unit_price: parseFloat(data.unit_price),
        discount_percent: parseFloat(data.discount_percent || '0'),
        vat_code: data.vat_code,
        delivery_date: data.delivery_date,
        notes: data.notes,
      }
      addLineMutation.mutate({ orderId: selectedOrder.id, line: lineData })
    }
  }

  const handleShipOrder = (data: any) => {
    if (selectedOrder?.id) {
      const shipData = {
        tracking_number: data.tracking_number,
        carrier: data.carrier,
        shipping_date: data.shipping_date || new Date().toISOString().split('T')[0],
      }
      shipMutation.mutate({ orderId: selectedOrder.id, shipData })
    }
  }

  const handleConvertToInvoice = (order: SalesOrder) => {
    if (order.id) {
      convertToInvoiceMutation.mutate(order.id)
    }
  }

  const handleEmailOrder = (data: any) => {
    if (selectedOrder?.id) {
      emailMutation.mutate({ orderId: selectedOrder.id, emailData: data })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading sales orders...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load sales orders</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['salesOrders'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
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
        data={orders || []}
        searchPlaceholder="Search sales orders..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Sales Order"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateOrder}
          onCancel={() => setShowCreateModal(false)}
          schema={salesOrderSchema}
          submitLabel="Create Order"
          loading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Sales Order"
        size="lg"
      >
        {selectedOrder && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditOrder}
            onCancel={() => setShowEditModal(false)}
            schema={salesOrderSchema}
            submitLabel="Update Order"
            loading={updateMutation.isPending}
            defaultValues={{
              customer_id: selectedOrder.customer_id.toString(),
              delivery_date: selectedOrder.delivery_date,
              reference: selectedOrder.reference,
              customer_order_no: selectedOrder.customer_order_no,
              delivery_address: selectedOrder.delivery_address,
              sales_rep: selectedOrder.sales_rep,
              payment_terms: selectedOrder.payment_terms,
              currency_code: selectedOrder.currency_code,
              notes: selectedOrder.notes,
            }}
          />
        )}
      </Modal>

      {/* Order Lines Modal */}
      <Modal
        isOpen={showLinesModal}
        onClose={() => setShowLinesModal(false)}
        title={`Order Lines - ${selectedOrder?.order_number}`}
        size="xl"
      >
        <div className="space-y-4">
          {selectedOrder?.status === 'DRAFT' && canEdit('sales') && (
            <div className="flex justify-end">
              <Button onClick={() => setShowAddLineModal(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Line
              </Button>
            </div>
          )}
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Line
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stock Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unit Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Discount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orderLines?.map((line) => (
                  <tr key={line.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {line.line_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.stock_code}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {line.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: selectedOrder?.currency_code || 'USD',
                      }).format(line.unit_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.discount_percent}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: selectedOrder?.currency_code || 'USD',
                      }).format(line.line_total || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {(!orderLines || orderLines.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              No lines added yet
            </div>
          )}
        </div>
      </Modal>

      {/* Add Line Modal */}
      <Modal
        isOpen={showAddLineModal}
        onClose={() => setShowAddLineModal(false)}
        title="Add Order Line"
        size="lg"
      >
        <FormBuilder
          fields={lineFormFields}
          onSubmit={handleAddLine}
          onCancel={() => setShowAddLineModal(false)}
          schema={orderLineSchema}
          submitLabel="Add Line"
          loading={addLineMutation.isPending}
        />
      </Modal>

      {/* Shipping Modal */}
      <Modal
        isOpen={showShippingModal}
        onClose={() => setShowShippingModal(false)}
        title={`Ship Order - ${selectedOrder?.order_number}`}
        size="lg"
      >
        <FormBuilder
          fields={shippingFormFields}
          onSubmit={handleShipOrder}
          onCancel={() => setShowShippingModal(false)}
          schema={shippingSchema}
          submitLabel="Ship Order"
          loading={shipMutation.isPending}
          defaultValues={{
            shipping_date: new Date().toISOString().split('T')[0],
          }}
        />
      </Modal>

      {/* Email Modal */}
      <Modal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
        title={`Email Order - ${selectedOrder?.order_number}`}
        size="lg"
      >
        <FormBuilder
          fields={emailFormFields}
          onSubmit={handleEmailOrder}
          onCancel={() => setShowEmailModal(false)}
          schema={emailSchema}
          submitLabel="Send Email"
          loading={emailMutation.isPending}
          defaultValues={{
            subject: `Sales Order ${selectedOrder?.order_number}`,
            message: `Dear Customer,\n\nPlease find your sales order ${selectedOrder?.order_number} attached.\n\nOrder Details:\n- Order Number: ${selectedOrder?.order_number}\n- Order Date: ${selectedOrder?.order_date ? new Date(selectedOrder.order_date).toLocaleDateString() : ''}\n- Delivery Date: ${selectedOrder?.delivery_date ? new Date(selectedOrder.delivery_date).toLocaleDateString() : 'TBD'}\n- Total Amount: ${selectedOrder?.total_amount ? new Intl.NumberFormat('en-US', { style: 'currency', currency: selectedOrder?.currency_code || 'USD' }).format(parseFloat(selectedOrder.total_amount.toString())) : ''}\n\nThank you for your business!\n\nBest regards,\nSales Team`,
          }}
        />
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setOrderToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Sales Order"
        message={`Are you sure you want to delete order ${orderToDelete?.order_number}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}