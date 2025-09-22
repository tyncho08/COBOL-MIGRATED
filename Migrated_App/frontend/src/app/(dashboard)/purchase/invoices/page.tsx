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
  PrinterIcon, 
  DocumentCheckIcon,
  ArrowPathIcon,
  ReceiptPercentIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface PurchaseInvoice {
  id: number
  invoice_number: string
  invoice_date: string
  invoice_type: string
  supplier_id: number
  supplier_code: string
  supplier_name: string
  supplier_reference?: string
  order_number?: string
  due_date: string
  goods_total: number
  vat_total: number
  gross_total: number
  amount_paid: number
  balance: number
  is_paid: boolean
  gl_posted: boolean
  invoice_status: string
  approval_status: string
  approved_by?: string
  approved_date?: string
}

// Schema
const purchaseInvoiceSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier is required'),
  invoice_type: z.string().min(1, 'Invoice type is required'),
  supplier_reference: z.string().min(1, 'Supplier reference is required'),
  order_number: z.string().optional(),
  payment_terms: z.string().optional(),
  notes: z.string().optional(),
  invoice_lines: z.array(z.object({
    stock_code: z.string().min(1, 'Stock code is required'),
    description: z.string().min(1, 'Description is required'),
    quantity: z.string().min(1, 'Quantity is required'),
    unit_cost: z.string().min(1, 'Unit cost is required'),
    vat_code: z.string().min(1, 'VAT code is required'),
  })).min(1, 'At least one invoice line is required'),
})

// Mock data
const mockPurchaseInvoices: PurchaseInvoice[] = [
  {
    id: 1,
    invoice_number: 'PIN001234',
    invoice_date: '2024-01-15',
    invoice_type: 'INVOICE',
    supplier_id: 1,
    supplier_code: 'SUPP001',
    supplier_name: 'ABC Supplies Ltd',
    supplier_reference: 'INV-2024-001',
    order_number: 'PO001234',
    due_date: '2024-02-14',
    goods_total: 2500.00,
    vat_total: 500.00,
    gross_total: 3000.00,
    amount_paid: 0.00,
    balance: 3000.00,
    is_paid: false,
    gl_posted: true,
    invoice_status: 'APPROVED',
    approval_status: 'APPROVED',
    approved_by: 'Manager',
    approved_date: '2024-01-16',
  },
  {
    id: 2,
    invoice_number: 'PIN001235',
    invoice_date: '2024-01-16',
    invoice_type: 'INVOICE',
    supplier_id: 2,
    supplier_code: 'SUPP002',
    supplier_name: 'Tech Components Inc',
    supplier_reference: 'TC-INV-456',
    order_number: 'PO001235',
    due_date: '2024-02-15',
    goods_total: 1200.00,
    vat_total: 240.00,
    gross_total: 1440.00,
    amount_paid: 1440.00,
    balance: 0.00,
    is_paid: true,
    gl_posted: true,
    invoice_status: 'PAID',
    approval_status: 'APPROVED',
    approved_by: 'Manager',
    approved_date: '2024-01-16',
  },
  {
    id: 3,
    invoice_number: 'PIN001236',
    invoice_date: '2024-01-17',
    invoice_type: 'CREDIT_NOTE',
    supplier_id: 3,
    supplier_code: 'SUPP003',
    supplier_name: 'Office Supplies Co',
    supplier_reference: 'CN-001',
    order_number: 'PO001236',
    due_date: '2024-02-16',
    goods_total: -200.00,
    vat_total: -40.00,
    gross_total: -240.00,
    amount_paid: 0.00,
    balance: -240.00,
    is_paid: false,
    gl_posted: false,
    invoice_status: 'PENDING',
    approval_status: 'PENDING',
  },
]

const getInvoiceTypeBadge = (type: string) => {
  switch (type) {
    case 'INVOICE':
      return <Badge variant="info">Invoice</Badge>
    case 'CREDIT_NOTE':
      return <Badge variant="warning">Credit Note</Badge>
    case 'DEBIT_NOTE':
      return <Badge variant="danger">Debit Note</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (status: string, isPaid: boolean) => {
  if (isPaid) {
    return <Badge variant="success">Paid</Badge>
  }
  
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'APPROVED':
      return <Badge variant="info">Approved</Badge>
    case 'REJECTED':
      return <Badge variant="danger">Rejected</Badge>
    case 'PAID':
      return <Badge variant="success">Paid</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getApprovalBadge = (status: string) => {
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">Pending Approval</Badge>
    case 'APPROVED':
      return <Badge variant="success">Approved</Badge>
    case 'REJECTED':
      return <Badge variant="danger">Rejected</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function PurchaseInvoicesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<PurchaseInvoice | null>(null)

  const { data: purchaseInvoices, isLoading } = useQuery({
    queryKey: ['purchase-invoices'],
    queryFn: () => Promise.resolve(mockPurchaseInvoices),
  })

  const columns: ColumnDef<PurchaseInvoice>[] = [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice Number',
    },
    {
      accessorKey: 'invoice_date',
      header: 'Invoice Date',
      cell: ({ row }) => {
        const date = row.getValue('invoice_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'invoice_type',
      header: 'Type',
      cell: ({ row }) => {
        return getInvoiceTypeBadge(row.getValue('invoice_type'))
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
      accessorKey: 'supplier_reference',
      header: 'Supplier Ref.',
    },
    {
      accessorKey: 'order_number',
      header: 'PO Number',
    },
    {
      accessorKey: 'due_date',
      header: 'Due Date',
      cell: ({ row }) => {
        const date = row.getValue('due_date') as string
        const dueDate = new Date(date)
        const today = new Date()
        const isOverdue = dueDate < today && !row.original.is_paid
        
        return (
          <span className={isOverdue ? 'text-red-600 font-semibold' : ''}>
            {dueDate.toLocaleDateString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'gross_total',
      header: 'Total',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('gross_total'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('balance'))
        const isCredit = amount < 0
        return (
          <span className={isCredit ? 'text-green-600' : amount > 0 ? 'text-red-600' : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(Math.abs(amount))}
            {isCredit && ' CR'}
          </span>
        )
      },
    },
    {
      accessorKey: 'approval_status',
      header: 'Approval',
      cell: ({ row }) => {
        return getApprovalBadge(row.getValue('approval_status'))
      },
    },
    {
      accessorKey: 'invoice_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('invoice_status'), row.original.is_paid)
      },
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const invoice = row.original
        return (
          <div className="flex space-x-1">
            {invoice.gl_posted && (
              <Badge variant="success" className="text-xs">GL</Badge>
            )}
            {invoice.approved_by && (
              <Badge variant="info" className="text-xs">APP</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const invoice = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedInvoice(invoice)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view invoice details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print invoice
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {invoice.approval_status === 'PENDING' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle approve invoice
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {!invoice.gl_posted && invoice.approval_status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle post to GL
                }}
              >
                <ReceiptPercentIcon className="h-4 w-4" />
              </Button>
            )}
            {invoice.gl_posted && invoice.invoice_status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle reverse invoice
                }}
              >
                <ArrowPathIcon className="h-4 w-4" />
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
      name: 'invoice_type',
      label: 'Invoice Type',
      type: 'select',
      required: true,
      options: [
        { value: 'INVOICE', label: 'Invoice' },
        { value: 'CREDIT_NOTE', label: 'Credit Note' },
        { value: 'DEBIT_NOTE', label: 'Debit Note' },
      ],
    },
    {
      name: 'supplier_reference',
      label: 'Supplier Reference',
      type: 'text',
      required: true,
    },
    {
      name: 'order_number',
      label: 'Purchase Order Number',
      type: 'text',
    },
    {
      name: 'payment_terms',
      label: 'Payment Terms (Days)',
      type: 'number',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateInvoice = (data: any) => {
    console.log('Creating purchase invoice:', data)
    setShowCreateModal(false)
  }

  const handleEditInvoice = (data: any) => {
    console.log('Editing purchase invoice:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Purchase Invoices"
        description="Manage supplier invoices and payments"
        breadcrumbs={[
          { label: 'Purchase Ledger', href: '/purchase' },
          { label: 'Purchase Invoices' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle aging report
              }}
            >
              Aging Report
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle batch approval
              }}
            >
              Batch Approve
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Invoice
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={purchaseInvoices || []}
        searchPlaceholder="Search purchase invoices..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Purchase Invoice"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateInvoice}
          onCancel={() => setShowCreateModal(false)}
          schema={purchaseInvoiceSchema}
          submitLabel="Create Invoice"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Purchase Invoice"
        size="xl"
      >
        {selectedInvoice && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditInvoice}
            onCancel={() => setShowEditModal(false)}
            schema={purchaseInvoiceSchema}
            submitLabel="Update Invoice"
            defaultValues={{
              supplier_code: selectedInvoice.supplier_code,
              invoice_type: selectedInvoice.invoice_type,
              supplier_reference: selectedInvoice.supplier_reference,
              order_number: selectedInvoice.order_number,
            }}
          />
        )}
      </Modal>
    </div>
  )
}