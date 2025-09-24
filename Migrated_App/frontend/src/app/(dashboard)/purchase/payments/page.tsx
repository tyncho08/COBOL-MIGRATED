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
  LinkIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  BanknotesIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface SupplierPayment {
  id: number
  payment_number: string
  payment_date: string
  supplier_id: number
  supplier_code: string
  supplier_name: string
  payment_method: string
  reference?: string
  payment_amount: number
  allocated_amount: number
  unallocated_amount: number
  bank_account?: string
  cheque_number?: string
  is_allocated: boolean
  is_reversed: boolean
  gl_posted: boolean
  notes?: string
}

// Schema
const supplierPaymentSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier is required'),
  payment_method: z.string().min(1, 'Payment method is required'),
  payment_amount: z.string().min(1, 'Payment amount is required'),
  reference: z.string().optional(),
  bank_account: z.string().optional(),
  cheque_number: z.string().optional(),
  notes: z.string().optional(),
})


const getPaymentMethodBadge = (method: string) => {
  switch (method) {
    case 'CASH':
      return <Badge variant="success">Cash</Badge>
    case 'CHEQUE':
      return <Badge variant="info">Cheque</Badge>
    case 'BANK_TRANSFER':
      return <Badge variant="default">Bank Transfer</Badge>
    case 'DIRECT_DEBIT':
      return <Badge variant="warning">Direct Debit</Badge>
    case 'CARD':
      return <Badge variant="warning">Card</Badge>
    default:
      return <Badge variant="default">{method}</Badge>
  }
}

const getAllocationBadge = (isAllocated: boolean, unallocatedAmount: number) => {
  if (isAllocated && unallocatedAmount === 0) {
    return <Badge variant="success">Fully Allocated</Badge>
  } else if (unallocatedAmount > 0) {
    return <Badge variant="warning">Partially Allocated</Badge>
  } else {
    return <Badge variant="danger">Unallocated</Badge>
  }
}

export default function SupplierPaymentsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showAllocationModal, setShowAllocationModal] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<SupplierPayment | null>(null)

  const { data: supplierPayments, isLoading } = useQuery({
    queryKey: ['supplier-payments'],
    queryFn: async () => {
      const response = await apiRequest('/api/v1/purchase/payments')
      if (!response.ok) {
        throw new Error('Failed to fetch supplier payments')
      }
      const result = await response.json()
      return result.data || []
    },
  })

  const columns: ColumnDef<SupplierPayment>[] = [
    {
      accessorKey: 'payment_number',
      header: 'Payment Number',
    },
    {
      accessorKey: 'payment_date',
      header: 'Payment Date',
      cell: ({ row }) => {
        const date = row.getValue('payment_date') as string
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
      accessorKey: 'payment_method',
      header: 'Method',
      cell: ({ row }) => {
        return getPaymentMethodBadge(row.getValue('payment_method'))
      },
    },
    {
      accessorKey: 'reference',
      header: 'Reference',
    },
    {
      accessorKey: 'cheque_number',
      header: 'Cheque #',
    },
    {
      accessorKey: 'payment_amount',
      header: 'Amount',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('payment_amount'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'allocated_amount',
      header: 'Allocated',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('allocated_amount'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'unallocated_amount',
      header: 'Unallocated',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('unallocated_amount'))
        return (
          <span className={amount > 0 ? 'text-orange-600 font-semibold' : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(amount)}
          </span>
        )
      },
    },
    {
      accessorKey: 'bank_account',
      header: 'Bank Account',
    },
    {
      id: 'allocation_status',
      header: 'Allocation',
      cell: ({ row }) => {
        const payment = row.original
        return getAllocationBadge(payment.is_allocated, payment.unallocated_amount)
      },
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const payment = row.original
        return (
          <div className="flex space-x-1">
            {payment.gl_posted && (
              <Badge variant="success" className="text-xs">GL</Badge>
            )}
            {payment.is_reversed && (
              <Badge variant="danger" className="text-xs">REV</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const payment = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedPayment(payment)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest(`/api/v1/purchase/payments/${payment.id}/view`)
                  const details = await response.json()
                  
                  const modal = document.createElement('div')
                  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                  modal.innerHTML = `
                    <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                      <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Payment Details</h2>
                      <div style="margin-bottom:1rem">
                        <strong>Payment Number:</strong> ${details.payment_number}<br>
                        <strong>Date:</strong> ${new Date(details.payment_date).toLocaleDateString()}<br>
                        <strong>Supplier:</strong> ${details.supplier_code} - ${details.supplier_name}<br>
                        <strong>Type:</strong> ${details.payment_type}<br>
                        <strong>Reference:</strong> ${details.reference || 'N/A'}<br>
                        <strong>Amount:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(details.payment_amount)}<br>
                        <strong>Allocated:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(details.allocated_amount)}<br>
                        <strong>Unallocated:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(details.unallocated_amount)}<br>
                        <strong>Status:</strong> ${details.payment_status}${details.is_reversed ? ' (Reversed)' : ''}
                        ${details.gl_posted ? '<br><strong>GL Posted:</strong> Yes' : ''}
                      </div>
                      <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                  `
                  document.body.appendChild(modal)
                  modal.onclick = (e) => {
                    if (e.target === modal) modal.remove()
                  }
                } catch (error) {
                  console.error('Error fetching payment details:', error)
                }
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            {payment.unallocated_amount > 0 && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedPayment(payment)
                  setShowAllocationModal(true)
                }}
              >
                <LinkIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest(`/api/v1/purchase/payments/${payment.id}/allocations`)
                  const allocations = await response.json()
                  
                  const modal = document.createElement('div')
                  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                  modal.innerHTML = `
                    <div style="background:white;padding:2rem;border-radius:8px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
                      <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Payment Allocations</h2>
                      <table style="width:100%;border-collapse:collapse">
                        <thead>
                          <tr style="border-bottom:2px solid #ccc">
                            <th style="padding:0.5rem;text-align:left">Invoice</th>
                            <th style="padding:0.5rem;text-align:left">Date</th>
                            <th style="padding:0.5rem;text-align:right">Invoice Amount</th>
                            <th style="padding:0.5rem;text-align:right">Allocated</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${allocations.map(a => `
                            <tr style="border-bottom:1px solid #eee">
                              <td style="padding:0.5rem">${a.invoice_number}</td>
                              <td style="padding:0.5rem">${new Date(a.allocation_date).toLocaleDateString()}</td>
                              <td style="padding:0.5rem;text-align:right">${new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(a.invoice_amount)}</td>
                              <td style="padding:0.5rem;text-align:right">${new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(a.allocated_amount)}</td>
                            </tr>
                          `).join('')}
                        </tbody>
                      </table>
                      <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;margin-top:1rem" onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                  `
                  document.body.appendChild(modal)
                  modal.onclick = (e) => {
                    if (e.target === modal) modal.remove()
                  }
                } catch (error) {
                  console.error('Error fetching allocations:', error)
                }
              }}
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
            {!payment.is_reversed && payment.gl_posted && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to reverse payment ${payment.payment_number}?`)) {
                    try {
                      const response = await apiRequest(`/api/v1/purchase/payments/${payment.id}/reverse`, {
                        method: 'POST'
                      })
                      if (response.ok) {
                        alert('Payment reversed successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to reverse payment')
                      }
                    } catch (error) {
                      console.error('Error reversing payment:', error)
                      alert('Error reversing payment')
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
      name: 'payment_method',
      label: 'Payment Method',
      type: 'select',
      required: true,
      options: [
        { value: 'CASH', label: 'Cash' },
        { value: 'CHEQUE', label: 'Cheque' },
        { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
        { value: 'DIRECT_DEBIT', label: 'Direct Debit' },
        { value: 'CARD', label: 'Card Payment' },
      ],
    },
    {
      name: 'payment_amount',
      label: 'Payment Amount',
      type: 'number',
      required: true,
    },
    {
      name: 'reference',
      label: 'Reference',
      type: 'text',
    },
    {
      name: 'bank_account',
      label: 'Bank Account',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'MAIN', label: 'Main Current Account' },
        { value: 'SAVINGS', label: 'Savings Account' },
        { value: 'PETTY', label: 'Petty Cash' },
      ],
    },
    {
      name: 'cheque_number',
      label: 'Cheque Number',
      type: 'text',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const allocationFields: FormField[] = [
    {
      name: 'allocations',
      label: 'Invoice Allocations',
      type: 'text', // This would be a custom component for allocation
    },
  ]

  const handleCreatePayment = (data: any) => {
    console.log('Creating supplier payment:', data)
    setShowCreateModal(false)
  }

  const handleEditPayment = (data: any) => {
    console.log('Editing supplier payment:', data)
    setShowEditModal(false)
  }

  const handleAllocation = (data: any) => {
    console.log('Allocating payment:', data)
    setShowAllocationModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Supplier Payments"
        description="Manage supplier payments and allocations"
        breadcrumbs={[
          { label: 'Purchase Ledger', href: '/purchase' },
          { label: 'Supplier Payments' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/purchase/payments/journal')
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Purchase Payments Journal</title></head>
                        <body>
                          <h1>Purchase Payments Journal</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Date</th><th>Reference</th><th>Supplier</th><th>Amount</th><th>Method</th></tr>
                            ${data.journal_entries?.map((entry: any) => 
                              `<tr><td>${entry.date}</td><td>${entry.reference}</td><td>${entry.supplier}</td><td>$${entry.amount.toFixed(2)}</td><td>${entry.payment_method}</td></tr>`
                            ).join('')}
                          </table>
                          <p><strong>Total Payments:</strong> $${data.total_payments?.toFixed(2) || '0.00'}</p>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  console.error('Failed to generate payment journal:', error)
                  alert('Failed to generate payment journal')
                }
              }}
            >
              <BanknotesIcon className="h-4 w-4 mr-2" />
              Payment Journal
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                if (confirm('Auto-allocate all unallocated supplier payments to outstanding invoices?')) {
                  try {
                    const response = await apiRequest('/api/v1/purchase/payments/auto-allocate', {
                      method: 'POST',
                      body: JSON.stringify([])
                    })
                    if (response.ok) {
                      const result = await response.json()
                      alert(`Auto-allocated ${result.allocated_count} payments totaling ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(result.amount_allocated)}`)
                      window.location.reload()
                    } else {
                      alert('Failed to auto-allocate payments')
                    }
                  } catch (error) {
                    console.error('Error auto-allocating payments:', error)
                    alert('Error auto-allocating payments')
                  }
                }
              }}
            >
              Auto Allocate
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Payment
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={supplierPayments || []}
        searchPlaceholder="Search payments..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Supplier Payment"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreatePayment}
          onCancel={() => setShowCreateModal(false)}
          schema={supplierPaymentSchema}
          submitLabel="Create Payment"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Supplier Payment"
        size="lg"
      >
        {selectedPayment && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditPayment}
            onCancel={() => setShowEditModal(false)}
            schema={supplierPaymentSchema}
            submitLabel="Update Payment"
            defaultValues={{
              supplier_code: selectedPayment.supplier_code,
              payment_method: selectedPayment.payment_method,
              payment_amount: selectedPayment.payment_amount.toString(),
              reference: selectedPayment.reference,
              bank_account: selectedPayment.bank_account,
              cheque_number: selectedPayment.cheque_number,
              notes: selectedPayment.notes,
            }}
          />
        )}
      </Modal>

      {/* Allocation Modal */}
      <Modal
        isOpen={showAllocationModal}
        onClose={() => setShowAllocationModal(false)}
        title="Allocate Payment to Invoices"
        size="xl"
      >
        {selectedPayment && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium">Payment Details</h3>
              <p>Payment Number: {selectedPayment.payment_number}</p>
              <p>Supplier: {selectedPayment.supplier_code} - {selectedPayment.supplier_name}</p>
              <p>Unallocated Amount: {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
              }).format(selectedPayment.unallocated_amount)}</p>
            </div>
            
            <div className="text-center py-8 text-gray-500">
              Allocation interface would be implemented here
              <br />
              showing outstanding invoices for the supplier
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAllocationModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleAllocation}>
                Save Allocations
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}