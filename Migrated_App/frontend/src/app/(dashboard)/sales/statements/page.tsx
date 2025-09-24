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
import { apiRequest } from '@/lib/utils/api'

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
    queryFn: async () => {
      const response = await apiRequest('/api/v1/master/customers')
      if (!response.ok) {
        throw new Error('Failed to fetch customers')
      }
      const result = await response.json()
      // Extract the data array from the response
      return result.data || []
    },
  })

  // Fetch statement entries for selected customer
  const { data: statementEntries } = useQuery({
    queryKey: ['statement-entries', selectedCustomer?.customer_code],
    queryFn: async () => {
      if (!selectedCustomer?.customer_code) return []
      
      const response = await apiRequest(`/api/v1/sales/statements/${selectedCustomer.customer_code}/entries`)
      if (!response.ok) {
        throw new Error('Failed to fetch statement entries')
      }
      return response.json()
    },
    enabled: !!selectedCustomer?.customer_code,
  })

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
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/sales/statements/generate', {
                    method: 'POST',
                    body: JSON.stringify({ 
                      customer_code: customer.customer_code,
                      format: 'pdf'
                    })
                  })
                  const blob = await response.blob()
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `statement-${customer.customer_code}-${new Date().toISOString().split('T')[0]}.pdf`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                  window.URL.revokeObjectURL(url)
                } catch (error) {
                  alert('Failed to print statement')
                }
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/sales/statements/email', {
                    method: 'POST',
                    body: JSON.stringify({ 
                      customer_code: customer.customer_code,
                      email: customer.email
                    })
                  })
                  const result = await response.json()
                  alert(`Statement emailed to ${customer.email}`)
                } catch (error) {
                  alert('Failed to email statement')
                }
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
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/master/customers/aged-debtors')
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Aged Debtors Report</title></head>
                        <body>
                          <h1>Aged Debtors Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Customer</th><th>Current</th><th>30 Days</th><th>60 Days</th><th>90+ Days</th><th>Total</th></tr>
                            ${data.report_data?.map((row: any) => 
                              `<tr><td>${row.customer}</td><td>$${row.current}</td><td>$${row['30_days']}</td><td>$${row['60_days']}</td><td>$${row['90_days']}</td><td>$${row.total}</td></tr>`
                            ).join('')}
                            <tr style="font-weight:bold"><td>TOTALS</td><td>$${data.totals?.current}</td><td>$${data.totals?.['30_days']}</td><td>$${data.totals?.['60_days']}</td><td>$${data.totals?.['90_days']}</td><td>$${data.totals?.total}</td></tr>
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                  alert('Aged debtors report generated')
                } catch (error) {
                  alert('Failed to generate aged debtors report')
                }
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
                data={statementEntries || []}
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
                  <Button 
                    variant="outline"
                    onClick={async () => {
                      if (selectedCustomer?.customer_code) {
                        try {
                          const response = await apiRequest('/api/v1/sales/statements/generate', {
                            method: 'POST',
                            body: JSON.stringify({
                              customer_code: selectedCustomer.customer_code,
                              from_date: formData.from_date || '2024-01-01',
                              to_date: formData.to_date || new Date().toISOString().split('T')[0],
                              include_paid: formData.include_paid || false
                            })
                          })
                          if (response.ok) {
                            const blob = await response.blob()
                            const url = window.URL.createObjectURL(blob)
                            const link = document.createElement('a')
                            link.href = url
                            link.download = `statement-${selectedCustomer.customer_code}-${new Date().toISOString().split('T')[0]}.pdf`
                            link.click()
                            window.URL.revokeObjectURL(url)
                          } else {
                            alert('Failed to generate statement')
                          }
                        } catch (error) {
                          console.error('Error printing statement:', error)
                          alert('Error printing statement')
                        }
                      }
                    }}
                  >
                    <PrinterIcon className="h-4 w-4 mr-2" />
                    Print
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      if (selectedCustomer) {
                        const modal = document.createElement('div')
                        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                        modal.innerHTML = `
                          <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                            <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Email Statement</h2>
                            <form id="emailForm">
                              <div style="margin-bottom:1rem">
                                <label style="display:block;margin-bottom:0.25rem">To:</label>
                                <input type="email" name="email" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="${selectedCustomer.email || ''}" required>
                              </div>
                              <div style="margin-bottom:1rem">
                                <label style="display:block;margin-bottom:0.25rem">Subject:</label>
                                <input type="text" name="subject" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="Statement of Account - ${selectedCustomer.customer_code}" required>
                              </div>
                              <div style="margin-bottom:1rem">
                                <label style="display:block;margin-bottom:0.25rem">Message:</label>
                                <textarea name="message" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" rows="4">Dear ${selectedCustomer.customer_name},\n\nPlease find attached your statement of account.\n\nBest regards,\nAccounts Department</textarea>
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
                          const emailFormData = new FormData(e.target)
                          try {
                            const response = await apiRequest('/api/v1/sales/statements/email', {
                              method: 'POST',
                              body: JSON.stringify({
                                customer_code: selectedCustomer.customer_code,
                                email: emailFormData.get('email'),
                                subject: emailFormData.get('subject'),
                                message: emailFormData.get('message'),
                                from_date: formData.from_date || '2024-01-01',
                                to_date: formData.to_date || new Date().toISOString().split('T')[0],
                                include_paid: formData.include_paid || false
                              })
                            })
                            if (response.ok) {
                              modal.remove()
                              alert('Statement emailed successfully')
                            } else {
                              alert('Failed to email statement')
                            }
                          } catch (error) {
                            console.error('Error emailing statement:', error)
                            alert('Error emailing statement')
                          }
                        }
                        modal.onclick = (e) => {
                          if (e.target === modal) modal.remove()
                        }
                      }
                    }}
                  >
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