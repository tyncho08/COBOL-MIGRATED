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
  EnvelopeIcon,
  ArrowPathIcon,
  DocumentCheckIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { salesApi, SalesInvoice } from '@/lib/api/sales'

// Schema
const salesInvoiceSchema = z.object({
  customer_code: z.string().min(1, 'Customer is required'),
  invoice_type: z.string().min(1, 'Invoice type is required'),
  customer_reference: z.string().optional(),
  order_number: z.string().optional(),
  delivery_note: z.string().optional(),
  payment_terms: z.string().optional(),
  settlement_discount: z.string().optional(),
  settlement_days: z.string().optional(),
  notes: z.string().optional(),
  invoice_lines: z.array(z.object({
    stock_code: z.string().min(1, 'Stock code is required'),
    description: z.string().min(1, 'Description is required'),
    quantity: z.string().min(1, 'Quantity is required'),
    unit_price: z.string().min(1, 'Unit price is required'),
    discount_percent: z.string().optional(),
    vat_code: z.string().min(1, 'VAT code is required'),
  })).min(1, 'At least one invoice line is required'),
})

// Data will come from API

const getInvoiceTypeBadge = (type: string) => {
  switch (type) {
    case 'INVOICE':
      return <Badge variant="info">Invoice</Badge>
    case 'CREDIT_NOTE':
      return <Badge variant="warning">Credit Note</Badge>
    case 'DEBIT_NOTE':
      return <Badge variant="danger">Debit Note</Badge>
    case 'PROFORMA':
      return <Badge variant="default">Proforma</Badge>
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
    case 'POSTED':
      return <Badge variant="info">Posted</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    case 'REVERSED':
      return <Badge variant="danger">Reversed</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function SalesInvoicesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState<SalesInvoice | null>(null)

  const { data: salesInvoices, isLoading, error } = useQuery({
    queryKey: ['sales-invoices'],
    queryFn: () => salesApi.invoices.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const columns: ColumnDef<SalesInvoice>[] = [
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
      accessorKey: 'order_number',
      header: 'Order #',
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
            {invoice.print_count > 0 && (
              <Badge variant="info" className="text-xs">P{invoice.print_count}</Badge>
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
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Invoice Details</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Invoice Number:</strong> ${invoice.invoice_number}<br>
                      <strong>Date:</strong> ${new Date(invoice.invoice_date).toLocaleDateString()}<br>
                      <strong>Customer:</strong> ${invoice.customer_code} - ${invoice.customer_name}<br>
                      <strong>Total:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(invoice.gross_total)}<br>
                      <strong>Balance:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(invoice.balance)}<br>
                      <strong>Status:</strong> ${invoice.invoice_status}${invoice.is_paid ? ' (Paid)' : ''}
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
                  const response = await fetch(`/api/v1/sales/invoices/${invoice.id}/print`, {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  if (response.ok) {
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `invoice-${invoice.invoice_number}.pdf`
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
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Email Invoice</h2>
                    <form id="emailForm">
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">To:</label>
                        <input type="email" name="to" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="" required>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Subject:</label>
                        <input type="text" name="subject" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="Invoice ${invoice.invoice_number}" required>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Message:</label>
                        <textarea name="message" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" rows="4">Please find attached invoice ${invoice.invoice_number}. Total amount due: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(invoice.balance)}</textarea>
                      </div>
                      <div style="display:flex;gap:0.5rem">
                        <button type="submit" style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Send</button>
                        <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Cancel</button>
                      </div>
                    </form>
                  </div>
                `
                document.body.appendChild(modal)
                modal.querySelector('#emailForm').onsubmit = async (e) => {
                  e.preventDefault()
                  const formData = new FormData(e.target)
                  try {
                    const response = await fetch(`/api/v1/sales/invoices/${invoice.id}/email`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                      },
                      body: JSON.stringify(Object.fromEntries(formData))
                    })
                    if (response.ok) {
                      modal.remove()
                      alert('Invoice emailed successfully')
                    }
                  } catch (error) {
                    console.error('Error emailing invoice:', error)
                  }
                }
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <EnvelopeIcon className="h-4 w-4" />
            </Button>
            {!invoice.gl_posted && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to post invoice ${invoice.invoice_number} to General Ledger?`)) {
                    try {
                      const response = await fetch(`/api/v1/sales/invoices/${invoice.id}/post-gl`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
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
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {invoice.gl_posted && invoice.invoice_status === 'POSTED' && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to reverse invoice ${invoice.invoice_number}? This will create a credit note.`)) {
                    try {
                      const response = await fetch(`/api/v1/sales/invoices/${invoice.id}/reverse`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({
                          reason: prompt('Enter reason for reversal:') || 'Customer request'
                        })
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
      name: 'invoice_type',
      label: 'Invoice Type',
      type: 'select',
      required: true,
      options: [
        { value: 'INVOICE', label: 'Invoice' },
        { value: 'CREDIT_NOTE', label: 'Credit Note' },
        { value: 'DEBIT_NOTE', label: 'Debit Note' },
        { value: 'PROFORMA', label: 'Proforma' },
      ],
    },
    {
      name: 'customer_reference',
      label: 'Customer Reference',
      type: 'text',
    },
    {
      name: 'order_number',
      label: 'Order Number',
      type: 'text',
    },
    {
      name: 'delivery_note',
      label: 'Delivery Note',
      type: 'text',
    },
    {
      name: 'payment_terms',
      label: 'Payment Terms (Days)',
      type: 'number',
    },
    {
      name: 'settlement_discount',
      label: 'Settlement Discount %',
      type: 'number',
    },
    {
      name: 'settlement_days',
      label: 'Settlement Days',
      type: 'number',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateInvoice = (data: any) => {
    console.log('Creating sales invoice:', data)
    setShowCreateModal(false)
  }

  const handleEditInvoice = (data: any) => {
    console.log('Editing sales invoice:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error loading sales invoices. Please try again later.</div>
  }

  return (
    <div>
      <PageHeader
        title="Sales Invoices"
        description="Manage sales invoices and track payments"
        breadcrumbs={[
          { label: 'Sales Ledger', href: '/sales' },
          { label: 'Sales Invoices' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/sales/invoices/aging-report', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  // Create a simple report display
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Sales Aging Report</title></head>
                        <body>
                          <h1>Sales Aging Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Customer</th><th>Current</th><th>30 Days</th><th>60 Days</th><th>90+ Days</th></tr>
                            ${data.report_data?.map((row: any) => 
                              `<tr><td>${row.customer}</td><td>$${row.current}</td><td>$${row['30_days']}</td><td>$${row['60_days']}</td><td>$${row['90_days']}</td></tr>`
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
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Invoice
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={salesInvoices || []}
        searchPlaceholder="Search invoices..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Sales Invoice"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateInvoice}
          onCancel={() => setShowCreateModal(false)}
          schema={salesInvoiceSchema}
          submitLabel="Create Invoice"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Sales Invoice"
        size="xl"
      >
        {selectedInvoice && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditInvoice}
            onCancel={() => setShowEditModal(false)}
            schema={salesInvoiceSchema}
            submitLabel="Update Invoice"
            defaultValues={{
              customer_code: selectedInvoice.customer_code,
              invoice_type: selectedInvoice.invoice_type,
              customer_reference: selectedInvoice.customer_reference,
              order_number: selectedInvoice.order_number,
            }}
          />
        )}
      </Modal>
    </div>
  )
}