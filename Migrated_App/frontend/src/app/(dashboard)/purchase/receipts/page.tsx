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
  TruckIcon,
  DocumentCheckIcon,
  ClipboardDocumentIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface GoodsReceipt {
  id: number
  receipt_number: string
  receipt_date: string
  supplier_id: number
  supplier_code: string
  supplier_name: string
  order_number?: string
  delivery_note?: string
  receipt_status: string
  total_quantity: number
  total_value: number
  goods_received: number
  outstanding_quantity: number
  is_complete: boolean
  gl_posted: boolean
  received_by: string
  notes?: string
}

// Schema
const goodsReceiptSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier is required'),
  order_number: z.string().optional(),
  delivery_note: z.string().optional(),
  notes: z.string().optional(),
  receipt_lines: z.array(z.object({
    stock_code: z.string().min(1, 'Stock code is required'),
    description: z.string().min(1, 'Description is required'),
    quantity_received: z.string().min(1, 'Quantity is required'),
    unit_cost: z.string().min(1, 'Unit cost is required'),
  })).min(1, 'At least one receipt line is required'),
})

// Mock data
const mockGoodsReceipts: GoodsReceipt[] = [
  {
    id: 1,
    receipt_number: 'GR001234',
    receipt_date: '2024-01-15',
    supplier_id: 1,
    supplier_code: 'SUPP001',
    supplier_name: 'ABC Supplies Ltd',
    order_number: 'PO001234',
    delivery_note: 'DEL-2024-001',
    receipt_status: 'RECEIVED',
    total_quantity: 100,
    total_value: 2500.00,
    goods_received: 100,
    outstanding_quantity: 0,
    is_complete: true,
    gl_posted: true,
    received_by: 'John Smith',
    notes: 'All items received in good condition',
  },
  {
    id: 2,
    receipt_number: 'GR001235',
    receipt_date: '2024-01-16',
    supplier_id: 2,
    supplier_code: 'SUPP002',
    supplier_name: 'Tech Components Inc',
    order_number: 'PO001235',
    delivery_note: 'DEL-2024-002',
    receipt_status: 'PARTIAL',
    total_quantity: 50,
    total_value: 1200.00,
    goods_received: 40,
    outstanding_quantity: 10,
    is_complete: false,
    gl_posted: false,
    received_by: 'Jane Doe',
    notes: 'Partial delivery - remaining items expected next week',
  },
  {
    id: 3,
    receipt_number: 'GR001236',
    receipt_date: '2024-01-17',
    supplier_id: 3,
    supplier_code: 'SUPP003',
    supplier_name: 'Office Supplies Co',
    order_number: 'PO001236',
    receipt_status: 'PENDING',
    total_quantity: 25,
    total_value: 750.00,
    goods_received: 0,
    outstanding_quantity: 25,
    is_complete: false,
    gl_posted: false,
    received_by: 'Bob Johnson',
    notes: 'Awaiting delivery',
  },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'PARTIAL':
      return <Badge variant="info">Partial</Badge>
    case 'RECEIVED':
      return <Badge variant="success">Received</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function GoodsReceiptsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedReceipt, setSelectedReceipt] = useState<GoodsReceipt | null>(null)

  const { data: goodsReceipts, isLoading } = useQuery({
    queryKey: ['goods-receipts'],
    queryFn: () => Promise.resolve(mockGoodsReceipts),
  })

  const columns: ColumnDef<GoodsReceipt>[] = [
    {
      accessorKey: 'receipt_number',
      header: 'Receipt Number',
    },
    {
      accessorKey: 'receipt_date',
      header: 'Receipt Date',
      cell: ({ row }) => {
        const date = row.getValue('receipt_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'supplier_code',
      header: 'Supplier',
    },
    {
      accessorKey: 'supplier_name',
      header: 'Supplier Name',
    },
    {
      accessorKey: 'order_number',
      header: 'PO Number',
    },
    {
      accessorKey: 'delivery_note',
      header: 'Delivery Note',
    },
    {
      accessorKey: 'total_quantity',
      header: 'Total Qty',
      cell: ({ row }) => {
        const quantity = row.getValue('total_quantity') as number
        return quantity.toLocaleString()
      },
    },
    {
      accessorKey: 'goods_received',
      header: 'Received',
      cell: ({ row }) => {
        const received = row.getValue('goods_received') as number
        const total = row.original.total_quantity
        return (
          <span className={received < total ? 'text-orange-600' : 'text-green-600'}>
            {received.toLocaleString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'outstanding_quantity',
      header: 'Outstanding',
      cell: ({ row }) => {
        const outstanding = row.getValue('outstanding_quantity') as number
        return (
          <span className={outstanding > 0 ? 'text-red-600 font-semibold' : ''}>
            {outstanding.toLocaleString()}
          </span>
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
      accessorKey: 'receipt_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('receipt_status'))
      },
    },
    {
      accessorKey: 'received_by',
      header: 'Received By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const receipt = row.original
        return (
          <div className="flex space-x-1">
            {receipt.gl_posted && (
              <Badge variant="success" className="text-xs">GL</Badge>
            )}
            {receipt.is_complete && (
              <Badge variant="info" className="text-xs">Complete</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const receipt = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedReceipt(receipt)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view receipt details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print receipt
              }}
            >
              <ClipboardDocumentIcon className="h-4 w-4" />
            </Button>
            {!receipt.gl_posted && receipt.is_complete && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle post to GL
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
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
        { value: 'SUPP001', label: 'SUPP001 - ABC Supplies Ltd' },
        { value: 'SUPP002', label: 'SUPP002 - Tech Components Inc' },
        { value: 'SUPP003', label: 'SUPP003 - Office Supplies Co' },
      ],
    },
    {
      name: 'order_number',
      label: 'Purchase Order Number',
      type: 'text',
    },
    {
      name: 'delivery_note',
      label: 'Delivery Note Number',
      type: 'text',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateReceipt = (data: any) => {
    console.log('Creating goods receipt:', data)
    setShowCreateModal(false)
  }

  const handleEditReceipt = (data: any) => {
    console.log('Editing goods receipt:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Goods Receipts"
        description="Manage incoming goods and deliveries"
        breadcrumbs={[
          { label: 'Purchase Ledger', href: '/purchase' },
          { label: 'Goods Receipts' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle goods received report
              }}
            >
              <TruckIcon className="h-4 w-4 mr-2" />
              Received Report
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Receipt
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={goodsReceipts || []}
        searchPlaceholder="Search goods receipts..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Goods Receipt"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateReceipt}
          onCancel={() => setShowCreateModal(false)}
          schema={goodsReceiptSchema}
          submitLabel="Create Receipt"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Goods Receipt"
        size="lg"
      >
        {selectedReceipt && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditReceipt}
            onCancel={() => setShowEditModal(false)}
            schema={goodsReceiptSchema}
            submitLabel="Update Receipt"
            defaultValues={{
              supplier_code: selectedReceipt.supplier_code,
              order_number: selectedReceipt.order_number,
              delivery_note: selectedReceipt.delivery_note,
              notes: selectedReceipt.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}