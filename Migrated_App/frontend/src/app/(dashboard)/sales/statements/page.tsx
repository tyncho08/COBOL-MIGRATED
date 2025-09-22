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
  PrinterIcon, 
  EnvelopeIcon, 
  EyeIcon,
  DocumentTextIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface Customer {
  id: number
  customer_code: string
  customer_name: string
  contact_person?: string
  email?: string
  phone?: string
  balance: number
  credit_limit: number
  payment_terms: string
  is_active: boolean
  on_hold: boolean
}

interface StatementEntry {
  date: string
  reference: string
  description: string
  debit: number
  credit: number
  balance: number
  type: string
}

// Schema
const statementRequestSchema = z.object({
  customer_codes: z.array(z.string()).min(1, 'At least one customer must be selected'),
  from_date: z.string().optional(),
  to_date: z.string().optional(),
  include_paid: z.boolean(),
  include_on_hold: z.boolean(),
  statement_date: z.string(),
  format: z.string(),
})

// Mock data
const mockCustomers: Customer[] = [
  {
    id: 1,
    customer_code: 'CUST001',
    customer_name: 'ABC Corporation',
    contact_person: 'John Smith',
    email: 'john@abc-corp.com',
    phone: '555-0123',
    balance: 1500.00,
    credit_limit: 10000.00,
    payment_terms: '30 DAYS',
    is_active: true,
    on_hold: false,
  },
  {
    id: 2,
    customer_code: 'CUST002',
    customer_name: 'XYZ Ltd',
    contact_person: 'Jane Doe',
    email: 'jane@xyz-ltd.com',
    phone: '555-0456',
    balance: 0.00,
    credit_limit: 5000.00,
    payment_terms: '30 DAYS',
    is_active: true,
    on_hold: false,
  },
  {
    id: 3,
    customer_code: 'CUST003',
    customer_name: 'Tech Solutions Inc',
    contact_person: 'Bob Johnson',
    email: 'bob@techsolutions.com',
    phone: '555-0789',
    balance: -600.00, // Credit balance
    credit_limit: 15000.00,
    payment_terms: '60 DAYS',
    is_active: true,
    on_hold: false,
  },
  {
    id: 4,
    customer_code: 'CUST004',
    customer_name: 'Slow Payer Ltd',
    contact_person: 'Mike Wilson',
    email: 'mike@slowpayer.com',
    phone: '555-0999',
    balance: 8500.00,
    credit_limit: 5000.00,
    payment_terms: '30 DAYS',
    is_active: true,
    on_hold: true,
  },
]

const getBalanceBadge = (balance: number, creditLimit: number, onHold: boolean) => {
  if (onHold) {
    return <Badge variant="danger">On Hold</Badge>
  }
  if (balance < 0) {
    return <Badge variant="success">Credit</Badge>
  }
  if (balance > creditLimit) {
    return <Badge variant="danger">Over Limit</Badge>
  }
  if (balance > creditLimit * 0.8) {
    return <Badge variant="warning">Near Limit</Badge>
  }
  return <Badge variant="info">Normal</Badge>
}

export default function CustomerStatementsPage() {
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [showStatementModal, setShowStatementModal] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([])

  const { data: customers, isLoading } = useQuery({
    queryKey: ['customers-for-statements'],
    queryFn: () => Promise.resolve(mockCustomers),
  })

  // Mock statement data
  const mockStatementEntries: StatementEntry[] = [
    {
      date: '2024-01-01',
      reference: 'B/FWD',
      description: 'Balance brought forward',
      debit: 0,
      credit: 0,
      balance: 500.00,
      type: 'BALANCE'
    },
    {
      date: '2024-01-05',
      reference: 'INV001234',
      description: 'Sales Invoice',
      debit: 3000.00,
      credit: 0,
      balance: 3500.00,
      type: 'INVOICE'
    },
    {
      date: '2024-01-15',
      reference: 'PAY001234',
      description: 'Payment received',
      debit: 0,
      credit: 1500.00,
      balance: 2000.00,
      type: 'PAYMENT'
    },
    {
      date: '2024-01-20',
      reference: 'CN001001',
      description: 'Credit note',
      debit: 0,
      credit: 500.00,
      balance: 1500.00,
      type: 'CREDIT'
    },
  ]

  const columns: ColumnDef<Customer>[] = [
    {
      accessorKey: 'customer_code',
      header: 'Customer Code',
    },
    {
      accessorKey: 'customer_name',
      header: 'Customer Name',
    },
    {
      accessorKey: 'contact_person',
      header: 'Contact',
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'phone',
      header: 'Phone',
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
      accessorKey: 'credit_limit',
      header: 'Credit Limit',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('credit_limit'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'payment_terms',
      header: 'Terms',
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const customer = row.original
        return getBalanceBadge(customer.balance, customer.credit_limit, customer.on_hold)
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const customer = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedCustomer(customer)
                setShowStatementModal(true)
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print statement
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle email statement
              }}
              disabled={!customer.email}
            >
              <EnvelopeIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const statementColumns: ColumnDef<StatementEntry>[] = [
    {
      accessorKey: 'date',
      header: 'Date',
      cell: ({ row }) => {
        const date = row.getValue('date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'reference',
      header: 'Reference',
    },
    {
      accessorKey: 'description',
      header: 'Description',
    },
    {
      accessorKey: 'debit',
      header: 'Debit',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('debit'))
        return amount > 0 ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount) : ''
      },
    },
    {
      accessorKey: 'credit',
      header: 'Credit',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('credit'))
        return amount > 0 ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount) : ''
      },
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('balance'))
        const isCredit = amount < 0
        return (
          <span className={isCredit ? 'text-green-600 font-semibold' : 'font-semibold'}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(Math.abs(amount))}
            {isCredit && ' CR'}
          </span>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'customer_codes',
      label: 'Customers',
      type: 'select',
      required: true,
      // This would be a multi-select component
      options: customers?.map(c => ({
        value: c.customer_code,
        label: `${c.customer_code} - ${c.customer_name}`
      })) || [],
    },
    {
      name: 'statement_date',
      label: 'Statement Date',
      type: 'date',
      required: true,
    },
    {
      name: 'from_date',
      label: 'From Date',
      type: 'date',
    },
    {
      name: 'to_date',
      label: 'To Date',
      type: 'date',
    },
    {
      name: 'include_paid',
      label: 'Include Paid Items',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'include_on_hold',
      label: 'Include On Hold Customers',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'format',
      label: 'Output Format',
      type: 'select',
      required: true,
      options: [
        { value: 'pdf', label: 'PDF' },
        { value: 'email', label: 'Email' },
        { value: 'print', label: 'Print' },
        { value: 'preview', label: 'Preview' },
      ],
    },
  ]

  const handleGenerateStatements = (data: any) => {
    console.log('Generating statements:', data)
    setShowGenerateModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Customer Statements"
        description="Generate and manage customer account statements"
        breadcrumbs={[
          { label: 'Sales Ledger', href: '/sales' },
          { label: 'Customer Statements' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle aged debtors report
              }}
            >
              Aged Debtors
            </Button>
            <Button onClick={() => setShowGenerateModal(true)}>
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Generate Statements
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={customers || []}
        searchPlaceholder="Search customers..."
      />

      {/* Generate Statements Modal */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="Generate Customer Statements"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleGenerateStatements}
          onCancel={() => setShowGenerateModal(false)}
          schema={statementRequestSchema}
          submitLabel="Generate Statements"
        />
      </Modal>

      {/* Statement Preview Modal */}
      <Modal
        isOpen={showStatementModal}
        onClose={() => setShowStatementModal(false)}
        title={`Statement Preview - ${selectedCustomer?.customer_name}`}
        size="xl"
      >
        {selectedCustomer && (
          <div className="space-y-6">
            {/* Customer Header */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-lg">{selectedCustomer.customer_name}</h3>
                  <p className="text-gray-600">Customer Code: {selectedCustomer.customer_code}</p>
                  <p className="text-gray-600">Contact: {selectedCustomer.contact_person}</p>
                  <p className="text-gray-600">Email: {selectedCustomer.email}</p>
                  <p className="text-gray-600">Phone: {selectedCustomer.phone}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Statement Date: {new Date().toLocaleDateString()}</p>
                  <p className="text-sm text-gray-600">Payment Terms: {selectedCustomer.payment_terms}</p>
                  <p className="text-sm text-gray-600">Credit Limit: {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                  }).format(selectedCustomer.credit_limit)}</p>
                  <p className="text-lg font-semibold mt-2">
                    Current Balance: {' '}
                    <span className={selectedCustomer.balance < 0 ? 'text-green-600' : 'text-red-600'}>
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      }).format(Math.abs(selectedCustomer.balance))}
                      {selectedCustomer.balance < 0 && ' CR'}
                    </span>
                  </p>
                </div>
              </div>
            </div>

            {/* Statement Entries */}
            <div>
              <h4 className="font-medium mb-4">Account Activity</h4>
              <DataTable
                columns={statementColumns}
                data={mockStatementEntries}
                searchPlaceholder=""
              />
            </div>

            {/* Statement Footer */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Statement generated on {new Date().toLocaleDateString()}
                </div>
                <div className="flex space-x-2">
                  <Button variant="outline">
                    <PrinterIcon className="h-4 w-4 mr-2" />
                    Print
                  </Button>
                  <Button variant="outline">
                    <EnvelopeIcon className="h-4 w-4 mr-2" />
                    Email
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}