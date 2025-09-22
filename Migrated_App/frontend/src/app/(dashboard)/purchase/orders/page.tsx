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
  TruckIcon,
  DocumentDuplicateIcon,
  PrinterIcon,
  EnvelopeIcon,
  TrashIcon,
  InboxIcon,
  ClipboardDocumentListIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { PurchaseOrder, PurchaseOrderLine, purchaseOrdersApi } from '@/lib/api/purchase-orders'
import { suppliersApi } from '@/lib/api/suppliers'
import { stockItemsApi } from '@/lib/api/stock-items'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

// Schema
const purchaseOrderSchema = z.object({
  supplier_id: z.string().min(1, 'Supplier is required'),
  delivery_date: z.string().optional(),
  reference: z.string().optional(),
  supplier_ref: z.string().optional(),
  delivery_address: z.string().optional(),
  buyer: z.string().optional(),
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

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'DRAFT':
      return <Badge variant="default">Draft</Badge>
    case 'APPROVED':
      return <Badge variant="success">Approved</Badge>
    case 'PARTIAL':
      return <Badge variant="warning">Partial</Badge>
    case 'RECEIVED':
      return <Badge variant="info">Received</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    case 'CLOSED':
      return <Badge variant="default">Closed</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function PurchaseOrdersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showLinesModal, setShowLinesModal] = useState(false)
  const [showAddLineModal, setShowAddLineModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null)
  const [orderToDelete, setOrderToDelete] = useState<PurchaseOrder | null>(null)
  
  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for purchase orders
  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['purchaseOrders'],
    queryFn: () => purchaseOrdersApi.getAll(),
  })

  // Query for suppliers
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => suppliersApi.getAll(),
  })

  // Query for stock items
  const { data: stockItems } = useQuery({
    queryKey: ['stockItems'],
    queryFn: () => stockItemsApi.getAll(),
  })

  // Query for order lines when viewing
  const { data: orderLines } = useQuery({
    queryKey: ['purchaseOrderLines', selectedOrder?.id],
    queryFn: () => selectedOrder?.id ? purchaseOrdersApi.getLines(selectedOrder.id) : null,
    enabled: !!selectedOrder?.id && showLinesModal,
  })

  // Mutation for creating purchase order
  const createMutation = useMutation({
    mutationFn: purchaseOrdersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      toast.success('Purchase order created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create purchase order')
    },
  })

  // Mutation for updating purchase order
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<PurchaseOrder> }) =>
      purchaseOrdersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      toast.success('Purchase order updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update purchase order')
    },
  })

  // Mutation for deleting purchase order
  const deleteMutation = useMutation({
    mutationFn: purchaseOrdersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      toast.success('Purchase order deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete purchase order')
    },
  })

  // Mutation for approving order
  const approveMutation = useMutation({
    mutationFn: purchaseOrdersApi.approve,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      toast.success('Purchase order approved successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve purchase order')
    },
  })

  // Mutation for cancelling order
  const cancelMutation = useMutation({
    mutationFn: purchaseOrdersApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      toast.success('Purchase order cancelled successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel purchase order')
    },
  })

  // Mutation for adding order line
  const addLineMutation = useMutation({
    mutationFn: ({ orderId, line }: { orderId: number; line: Omit<PurchaseOrderLine, 'id'> }) =>
      purchaseOrdersApi.addLine(orderId, line),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })
      queryClient.invalidateQueries({ queryKey: ['purchaseOrderLines'] })
      toast.success('Line added successfully')
      setShowAddLineModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add line')
    },
  })

  const columns: ColumnDef<PurchaseOrder>[] = [
    {
      accessorKey: 'order_number',
      header: 'Order Number',
    },
    {
      accessorKey: 'supplier_code',
      header: 'Supplier',
      cell: ({ row }) => {
        const order = row.original
        return (
          <div>
            <div className="font-medium">{order.supplier_code}</div>
            {order.supplier_name && (
              <div className="text-sm text-gray-500">{order.supplier_name}</div>
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
      accessorKey: 'supplier_ref',
      header: 'Supplier Ref',
      cell: ({ row }) => row.getValue('supplier_ref') || '-',
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
        const canApprove = order.status === 'DRAFT' && canEdit('purchase')
        const canCancel = ['DRAFT', 'APPROVED'].includes(order.status) && canEdit('purchase')
        const canReceive = order.status === 'APPROVED' && canEdit('purchase')
        
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
            {canApprove && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleApprove(order)}
                title="Approve Order"
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
            {canReceive && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  toast('Goods receipt functionality coming soon')
                }}
                title="Receive Goods"
              >
                <TruckIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await purchaseOrdersApi.print(order.id!)
                  toast.success('Order printed')
                } catch (error) {
                  toast.error('Failed to print order')
                }
              }}
              title="Print"
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {order.supplier_name && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  toast('Email functionality coming soon')
                }}
                title="Email Order"
              >
                <EnvelopeIcon className="h-4 w-4" />
              </Button>
            )}
            {order.status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  toast('Convert to invoice coming soon')
                }}
                title="Convert to Invoice"
              >
                <DocumentDuplicateIcon className="h-4 w-4" />
              </Button>
            )}
            {canDelete('purchase') && order.status === 'DRAFT' && (
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
      name: 'supplier_id',
      label: 'Supplier',
      type: 'select',
      required: true,
      options: Array.isArray(suppliers) 
        ? suppliers.map((s: any) => ({ 
            value: s.id!.toString(), 
            label: `${s.supplier_code} - ${s.supplier_name}` 
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
      name: 'supplier_ref',
      label: 'Supplier Reference',
      type: 'text',
    },
    {
      name: 'delivery_address',
      label: 'Delivery Address',
      type: 'textarea',
    },
    {
      name: 'buyer',
      label: 'Buyer',
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

  const handleCreateOrder = (data: any) => {
    const orderData = {
      ...data,
      supplier_id: parseInt(data.supplier_id),
      order_date: new Date().toISOString().split('T')[0],
      exchange_rate: 1,
      status: 'DRAFT' as const,
      order_lines: [],
      supplier_code: suppliers?.find(s => s.id === parseInt(data.supplier_id))?.supplier_code || '',
    }
    createMutation.mutate(orderData)
  }

  const handleEditOrder = (data: any) => {
    if (selectedOrder?.id) {
      const orderData = {
        ...data,
        supplier_id: parseInt(data.supplier_id),
        supplier_code: suppliers?.find(s => s.id === parseInt(data.supplier_id))?.supplier_code || '',
      }
      updateMutation.mutate({ id: selectedOrder.id, data: orderData })
    }
  }

  const handleDeleteOrder = (order: PurchaseOrder) => {
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

  const handleApprove = (order: PurchaseOrder) => {
    if (order.id) {
      approveMutation.mutate(order.id)
    }
  }

  const handleCancel = (order: PurchaseOrder) => {
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading purchase orders...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load purchase orders</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
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
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                toast('Order suggestions coming soon')
              }}
            >
              <ShoppingCartIcon className="h-4 w-4 mr-2" />
              Order Suggestions
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                toast('Pending receipts coming soon')
              }}
            >
              <InboxIcon className="h-4 w-4 mr-2" />
              Pending Receipts
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Purchase Order
            </Button>
          </div>
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
          loading={createMutation.isPending}
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
            loading={updateMutation.isPending}
            defaultValues={{
              supplier_id: selectedOrder.supplier_id.toString(),
              delivery_date: selectedOrder.delivery_date,
              reference: selectedOrder.reference,
              supplier_ref: selectedOrder.supplier_ref,
              delivery_address: selectedOrder.delivery_address,
              buyer: selectedOrder.buyer,
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
          {selectedOrder?.status === 'DRAFT' && canEdit('purchase') && (
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Received
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.received_quantity || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedOrder?.status === 'DRAFT' && canEdit('purchase') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            toast('Edit line coming soon')
                          }}
                        >
                          <PencilIcon className="h-4 w-4" />
                        </Button>
                      )}
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

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setOrderToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Purchase Order"
        message={`Are you sure you want to delete order ${orderToDelete?.order_number}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}