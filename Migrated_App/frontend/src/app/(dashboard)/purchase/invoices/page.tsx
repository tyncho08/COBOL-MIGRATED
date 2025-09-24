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
import { apiRequest } from '@/lib/utils/api'
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
    queryFn: async () => {
      const response = await apiRequest('/api/v1/purchase/invoices')
      if (!response.ok) {
        throw new Error('Failed to fetch purchase invoices')
      }
      const result = await response.json()
      return result.data || []
    },
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
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Purchase Invoice Details</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Invoice Number:</strong> ${invoice.invoice_number}<br>
                      <strong>Date:</strong> ${new Date(invoice.invoice_date).toLocaleDateString()}<br>
                      <strong>Supplier:</strong> ${invoice.supplier_code} - ${invoice.supplier_name}<br>
                      <strong>Order Number:</strong> ${invoice.order_number || 'N/A'}<br>
                      <strong>Receipt Number:</strong> ${invoice.receipt_number || 'N/A'}<br>
                      <strong>Total:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(invoice.gross_total)}<br>
                      <strong>Balance:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(invoice.balance)}<br>
                      <strong>Status:</strong> ${invoice.invoice_status}${invoice.is_paid ? ' (Paid)' : ''}
                      ${invoice.gl_posted ? '<br><strong>GL Posted:</strong> Yes' : ''}
                      ${invoice.is_approved ? '<br><strong>Approved:</strong> Yes' : ''}
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
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest(`/api/v1/purchase/invoices/${invoice.id}/print`)
                  if (response.ok) {
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `purchase-invoice-${invoice.invoice_number}.pdf`
                    link.click()
                    window.URL.revokeObjectURL(url)
                  } else {
                    console.error('Failed to print invoice')
                  }
                } catch (error) {
                  console.error('Error printing invoice:', error)
                }
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {invoice.approval_status === 'PENDING' && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to approve invoice ${invoice.invoice_number}?`)) {
                    try {
                      const response = await apiRequest(`/api/v1/purchase/invoices/${invoice.id}/approve`, {
                        method: 'POST'
                      })
                      if (response.ok) {
                        alert('Invoice approved successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to approve invoice')
                      }
                    } catch (error) {
                      console.error('Error approving invoice:', error)
                      alert('Error approving invoice')
                    }
                  }
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {!invoice.gl_posted && invoice.approval_status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to post invoice ${invoice.invoice_number} to General Ledger?`)) {
                    try {
                      const response = await apiRequest(`/api/v1/purchase/invoices/${invoice.id}/post-gl`, {
                        method: 'POST'
                      })
                      if (response.ok) {
                        alert('Invoice posted to GL successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to post invoice to GL')
                      }
                    } catch (error) {
                      console.error('Error posting to GL:', error)
                      alert('Error posting invoice to GL')
                    }
                  }
                }}
              >
                <ReceiptPercentIcon className="h-4 w-4" />
              </Button>
            )}
            {invoice.gl_posted && invoice.invoice_status === 'APPROVED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to reverse invoice ${invoice.invoice_number}?`)) {
                    try {
                      const response = await apiRequest(`/api/v1/purchase/invoices/${invoice.id}/reverse`, {
                        method: 'POST'
                      })
                      if (response.ok) {
                        alert('Invoice reversed successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to reverse invoice')
                      }
                    } catch (error) {
                      console.error('Error reversing invoice:', error)
                      alert('Error reversing invoice')
                    }
                  }
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
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/purchase/invoices/aging-report')
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Purchase Aging Report</title></head>
                        <body>
                          <h1>Purchase Aging Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Supplier</th><th>Current</th><th>30 Days</th><th>60 Days</th><th>90+ Days</th></tr>
                            ${data.report_data?.map((row: any) => 
                              `<tr><td>${row.supplier}</td><td>$${row.current}</td><td>$${row['30_days']}</td><td>$${row['60_days']}</td><td>$${row['90_days']}</td></tr>`
                            ).join('')}
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  console.error('Failed to generate aging report:', error)
                }
              }}
            >
              Aging Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  // Get selected invoice IDs (would need to implement selection in DataTable)
                  const selectedIds = [1, 2, 3] // Mock for now
                  const response = await apiRequest('/api/v1/purchase/invoices/batch-approve', {
                    method: 'POST',
                    body: JSON.stringify(selectedIds)
                  })
                  const result = await response.json()
                  alert(`Approved ${result.approved_count} invoices`)
                } catch (error) {
                  console.error('Failed to batch approve:', error)
                }
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