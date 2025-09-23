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
  LinkIcon,
  ArrowPathIcon,
  DocumentTextIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { salesApi } from '@/lib/api/sales'

// Types - CustomerPayment interface should match salesApi
interface CustomerPayment {
  id: number
  payment_number: string
  payment_date: string
  customer_id: number
  customer_code: string
  customer_name: string
  payment_method: string
  reference?: string
  payment_amount: number
  allocated_amount: number
  unallocated_amount: number
  bank_account?: string
  bank_reference?: string
  is_allocated: boolean
  is_reversed: boolean
  gl_posted: boolean
  notes?: string
}

// Schema
const customerPaymentSchema = z.object({
  customer_code: z.string().min(1, 'Customer is required'),
  payment_method: z.string().min(1, 'Payment method is required'),
  payment_amount: z.string().min(1, 'Payment amount is required'),
  reference: z.string().optional(),
  bank_account: z.string().optional(),
  bank_reference: z.string().optional(),
  notes: z.string().optional(),
})

// Data will come from API

const getPaymentMethodBadge = (method: string) => {
  switch (method) {
    case 'CASH':
      return <Badge variant="success">Cash</Badge>
    case 'CHEQUE':
      return <Badge variant="info">Cheque</Badge>
    case 'BANK_TRANSFER':
      return <Badge variant="default">Bank Transfer</Badge>
    case 'CARD':
      return <Badge variant="warning">Card</Badge>
    case 'DIRECT_DEBIT':
      return <Badge variant="info">Direct Debit</Badge>
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

export default function CustomerPaymentsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showAllocationModal, setShowAllocationModal] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<CustomerPayment | null>(null)

  const { data: customerPayments, isLoading, error } = useQuery({
    queryKey: ['customer-payments'],
    queryFn: () => salesApi.payments.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const columns: ColumnDef<CustomerPayment>[] = [
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
      accessorKey: 'customer_code',
      header: 'Customer',
    },
    {
      accessorKey: 'customer_name',
      header: 'Customer Name',
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
              onClick={() => {
                // Handle view payment details
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
              onClick={() => {
                // Handle view allocation details
              }}
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
            {!payment.is_reversed && payment.gl_posted && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle reverse payment
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
      name: 'payment_method',
      label: 'Payment Method',
      type: 'select',
      required: true,
      options: [
        { value: 'CASH', label: 'Cash' },
        { value: 'CHEQUE', label: 'Cheque' },
        { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
        { value: 'CARD', label: 'Card Payment' },
        { value: 'DIRECT_DEBIT', label: 'Direct Debit' },
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
      name: 'bank_reference',
      label: 'Bank Reference',
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
    console.log('Creating customer payment:', data)
    setShowCreateModal(false)
  }

  const handleEditPayment = (data: any) => {
    console.log('Editing customer payment:', data)
    setShowEditModal(false)
  }

  const handleAllocation = (data: any) => {
    console.log('Allocating payment:', data)
    setShowAllocationModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error loading customer payments. Please try again later.</div>
  }

  return (
    <div>
      <PageHeader
        title="Customer Payments"
        description="Manage customer payments and allocations"
        breadcrumbs={[
          { label: 'Sales Ledger', href: '/sales' },
          { label: 'Customer Payments' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle cash receipts journal
              }}
            >
              Cash Journal
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle auto-allocation
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
        data={customerPayments || []}
        searchPlaceholder="Search payments..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Customer Payment"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreatePayment}
          onCancel={() => setShowCreateModal(false)}
          schema={customerPaymentSchema}
          submitLabel="Create Payment"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Customer Payment"
        size="lg"
      >
        {selectedPayment && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditPayment}
            onCancel={() => setShowEditModal(false)}
            schema={customerPaymentSchema}
            submitLabel="Update Payment"
            defaultValues={{
              customer_code: selectedPayment.customer_code,
              payment_method: selectedPayment.payment_method,
              payment_amount: selectedPayment.payment_amount.toString(),
              reference: selectedPayment.reference,
              bank_account: selectedPayment.bank_account,
              bank_reference: selectedPayment.bank_reference,
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
              <p>Customer: {selectedPayment.customer_code} - {selectedPayment.customer_name}</p>
              <p>Unallocated Amount: {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
              }).format(selectedPayment.unallocated_amount)}</p>
            </div>
            
            <div className="text-center py-8 text-gray-500">
              Allocation interface would be implemented here
              <br />
              showing outstanding invoices for the customer
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