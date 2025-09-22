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
  EnvelopeIcon,
  PhoneIcon,
  UsersIcon,
  DocumentTextIcon,
  CreditCardIcon,
  ChartBarIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface Customer {
  id: number
  customer_code: string
  customer_name: string
  contact_person?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  phone?: string
  fax?: string
  email?: string
  website?: string
  tax_number?: string
  payment_terms: string
  currency_code: string
  credit_limit: number
  balance: number
  ytd_sales: number
  discount_percent: number
  is_active: boolean
  on_hold: boolean
  customer_type: string
  sales_rep?: string
  price_list?: string
  notes?: string
  created_date: string
  last_sale_date?: string
}

// Schema
const customerSchema = z.object({
  customer_code: z.string().min(1, 'Customer code is required'),
  customer_name: z.string().min(1, 'Customer name is required'),
  contact_person: z.string().optional(),
  address_line1: z.string().optional(),
  address_line2: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  postal_code: z.string().optional(),
  country: z.string().optional(),
  phone: z.string().optional(),
  fax: z.string().optional(),
  email: z.string().email('Invalid email format').optional().or(z.literal('')),
  website: z.string().optional(),
  tax_number: z.string().optional(),
  payment_terms: z.string().min(1, 'Payment terms are required'),
  currency_code: z.string().min(1, 'Currency is required'),
  credit_limit: z.string().optional(),
  discount_percent: z.string().optional(),
  customer_type: z.string().min(1, 'Customer type is required'),
  sales_rep: z.string().optional(),
  price_list: z.string().optional(),
  notes: z.string().optional(),
})

// Mock data
const mockCustomers: Customer[] = [
  {
    id: 1,
    customer_code: 'CUST001',
    customer_name: 'ABC Corporation',
    contact_person: 'John Smith',
    address_line1: '123 Business Avenue',
    address_line2: 'Suite 100',
    city: 'New York',
    state: 'NY',
    postal_code: '10001',
    country: 'USA',
    phone: '+1 555-0123',
    fax: '+1 555-0124',
    email: 'accounts@abc-corp.com',
    website: 'www.abc-corp.com',
    tax_number: '12-3456789',
    payment_terms: '30 DAYS',
    currency_code: 'USD',
    credit_limit: 100000.00,
    balance: 25000.00,
    ytd_sales: 350000.00,
    discount_percent: 5.0,
    is_active: true,
    on_hold: false,
    customer_type: 'CORPORATE',
    sales_rep: 'Alice Johnson',
    price_list: 'STANDARD',
    created_date: '2024-01-01',
    last_sale_date: '2024-01-15',
  },
  {
    id: 2,
    customer_code: 'CUST002',
    customer_name: 'XYZ Ltd',
    contact_person: 'Jane Doe',
    address_line1: '456 Commerce Street',
    city: 'Los Angeles',
    state: 'CA',
    postal_code: '90210',
    country: 'USA',
    phone: '+1 555-0456',
    email: 'finance@xyz-ltd.com',
    tax_number: '98-7654321',
    payment_terms: '60 DAYS',
    currency_code: 'USD',
    credit_limit: 75000.00,
    balance: 12500.00,
    ytd_sales: 180000.00,
    discount_percent: 3.0,
    is_active: true,
    on_hold: false,
    customer_type: 'BUSINESS',
    sales_rep: 'Bob Wilson',
    price_list: 'STANDARD',
    created_date: '2024-01-01',
    last_sale_date: '2024-01-12',
  },
  {
    id: 3,
    customer_code: 'CUST003',
    customer_name: 'Tech Solutions Inc',
    contact_person: 'Bob Johnson',
    address_line1: '789 Technology Way',
    city: 'San Francisco',
    state: 'CA',
    postal_code: '94105',
    country: 'USA',
    phone: '+1 555-0789',
    email: 'orders@techsolutions.com',
    tax_number: '55-9876543',
    payment_terms: '15 DAYS',
    currency_code: 'USD',
    credit_limit: 50000.00,
    balance: -5000.00, // Credit balance
    ytd_sales: 95000.00,
    discount_percent: 10.0,
    is_active: true,
    on_hold: false,
    customer_type: 'CORPORATE',
    sales_rep: 'Charlie Brown',
    price_list: 'VOLUME',
    notes: 'VIP customer - expedited shipping',
    created_date: '2024-01-01',
    last_sale_date: '2024-01-14',
  },
  {
    id: 4,
    customer_code: 'CUST004',
    customer_name: 'Slow Payer Ltd',
    contact_person: 'Mike Wilson',
    address_line1: '321 Payment Street',
    city: 'Chicago',
    state: 'IL',
    postal_code: '60601',
    country: 'USA',
    phone: '+1 555-0999',
    email: 'mike@slowpayer.com',
    tax_number: '77-1234567',
    payment_terms: '30 DAYS',
    currency_code: 'USD',
    credit_limit: 25000.00,
    balance: 35000.00, // Over credit limit
    ytd_sales: 65000.00,
    discount_percent: 0.0,
    is_active: true,
    on_hold: true,
    customer_type: 'BUSINESS',
    sales_rep: 'Alice Johnson',
    price_list: 'STANDARD',
    notes: 'Payment issues - on hold until balance reduced',
    created_date: '2024-01-01',
    last_sale_date: '2024-01-08',
  },
]

const getCustomerTypeBadge = (type: string) => {
  switch (type) {
    case 'CORPORATE':
      return <Badge variant="info">Corporate</Badge>
    case 'BUSINESS':
      return <Badge variant="success">Business</Badge>
    case 'INDIVIDUAL':
      return <Badge variant="warning">Individual</Badge>
    case 'GOVERNMENT':
      return <Badge variant="secondary">Government</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (isActive: boolean, onHold: boolean, balance: number, creditLimit: number) => {
  if (onHold) {
    return <Badge variant="danger">On Hold</Badge>
  }
  if (!isActive) {
    return <Badge variant="default">Inactive</Badge>
  }
  if (balance > creditLimit && creditLimit > 0) {
    return <Badge variant="warning">Over Limit</Badge>
  }
  return <Badge variant="success">Active</Badge>
}

export default function CustomersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)

  const { data: customers, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: () => Promise.resolve(mockCustomers),
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
      header: 'Contact Person',
    },
    {
      accessorKey: 'city',
      header: 'City',
    },
    {
      accessorKey: 'state',
      header: 'State',
    },
    {
      accessorKey: 'phone',
      header: 'Phone',
    },
    {
      accessorKey: 'email',
      header: 'Email',
    },
    {
      accessorKey: 'payment_terms',
      header: 'Terms',
    },
    {
      accessorKey: 'currency_code',
      header: 'Currency',
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
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('balance'))
        const creditLimit = row.original.credit_limit
        const isOverLimit = amount > creditLimit && creditLimit > 0
        const isCredit = amount < 0
        
        return (
          <span className={
            isOverLimit ? 'text-red-600 font-bold' : 
            isCredit ? 'text-green-600' : 
            amount > 0 ? 'text-orange-600' : ''
          }>
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
      accessorKey: 'ytd_sales',
      header: 'YTD Sales',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('ytd_sales'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'discount_percent',
      header: 'Discount %',
      cell: ({ row }) => {
        const percent = parseFloat(row.getValue('discount_percent'))
        return `${percent.toFixed(1)}%`
      },
    },
    {
      accessorKey: 'customer_type',
      header: 'Type',
      cell: ({ row }) => {
        return getCustomerTypeBadge(row.getValue('customer_type'))
      },
    },
    {
      accessorKey: 'sales_rep',
      header: 'Sales Rep',
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const customer = row.original
        return getStatusBadge(customer.is_active, customer.on_hold, customer.balance, customer.credit_limit)
      },
    },
    {
      accessorKey: 'last_sale_date',
      header: 'Last Sale',
      cell: ({ row }) => {
        const date = row.getValue('last_sale_date') as string
        return date ? new Date(date).toLocaleDateString() : 'Never'
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
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view customer details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle customer statement
              }}
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle sales analysis
              }}
            >
              <ChartBarIcon className="h-4 w-4" />
            </Button>
            {customer.email && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle email customer
                }}
              >
                <EnvelopeIcon className="h-4 w-4" />
              </Button>
            )}
            {customer.phone && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle call customer
                }}
              >
                <PhoneIcon className="h-4 w-4" />
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
      label: 'Customer Code',
      type: 'text',
      required: true,
    },
    {
      name: 'customer_name',
      label: 'Customer Name',
      type: 'text',
      required: true,
    },
    {
      name: 'contact_person',
      label: 'Contact Person',
      type: 'text',
    },
    {
      name: 'address_line1',
      label: 'Address Line 1',
      type: 'text',
    },
    {
      name: 'address_line2',
      label: 'Address Line 2',
      type: 'text',
    },
    {
      name: 'city',
      label: 'City',
      type: 'text',
    },
    {
      name: 'state',
      label: 'State/Province',
      type: 'text',
    },
    {
      name: 'postal_code',
      label: 'Postal Code',
      type: 'text',
    },
    {
      name: 'country',
      label: 'Country',
      type: 'select',
      options: [
        { value: 'USA', label: 'United States' },
        { value: 'CAN', label: 'Canada' },
        { value: 'GBR', label: 'United Kingdom' },
        { value: 'DEU', label: 'Germany' },
        { value: 'FRA', label: 'France' },
      ],
    },
    {
      name: 'phone',
      label: 'Phone',
      type: 'text',
    },
    {
      name: 'fax',
      label: 'Fax',
      type: 'text',
    },
    {
      name: 'email',
      label: 'Email',
      type: 'email',
    },
    {
      name: 'website',
      label: 'Website',
      type: 'text',
    },
    {
      name: 'tax_number',
      label: 'Tax Number',
      type: 'text',
    },
    {
      name: 'payment_terms',
      label: 'Payment Terms',
      type: 'select',
      required: true,
      options: [
        { value: '7 DAYS', label: '7 Days' },
        { value: '14 DAYS', label: '14 Days' },
        { value: '15 DAYS', label: '15 Days' },
        { value: '30 DAYS', label: '30 Days' },
        { value: '60 DAYS', label: '60 Days' },
        { value: '90 DAYS', label: '90 Days' },
        { value: 'COD', label: 'Cash on Delivery' },
        { value: 'PREPAID', label: 'Prepaid' },
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
        { value: 'CAD', label: 'Canadian Dollar' },
      ],
    },
    {
      name: 'credit_limit',
      label: 'Credit Limit',
      type: 'number',
    },
    {
      name: 'discount_percent',
      label: 'Discount Percentage',
      type: 'number',
    },
    {
      name: 'customer_type',
      label: 'Customer Type',
      type: 'select',
      required: true,
      options: [
        { value: 'CORPORATE', label: 'Corporate' },
        { value: 'BUSINESS', label: 'Business' },
        { value: 'INDIVIDUAL', label: 'Individual' },
        { value: 'GOVERNMENT', label: 'Government' },
      ],
    },
    {
      name: 'sales_rep',
      label: 'Sales Representative',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'Alice Johnson', label: 'Alice Johnson' },
        { value: 'Bob Wilson', label: 'Bob Wilson' },
        { value: 'Charlie Brown', label: 'Charlie Brown' },
        { value: 'Diana Prince', label: 'Diana Prince' },
      ],
    },
    {
      name: 'price_list',
      label: 'Price List',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'STANDARD', label: 'Standard Pricing' },
        { value: 'VOLUME', label: 'Volume Pricing' },
        { value: 'PREMIUM', label: 'Premium Pricing' },
        { value: 'WHOLESALE', label: 'Wholesale Pricing' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateCustomer = (data: any) => {
    console.log('Creating customer:', data)
    setShowCreateModal(false)
  }

  const handleEditCustomer = (data: any) => {
    console.log('Editing customer:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Customers"
        description="Manage customer information and relationships"
        breadcrumbs={[
          { label: 'Master Data', href: '/master' },
          { label: 'Customers' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle customer report
              }}
            >
              <UsersIcon className="h-4 w-4 mr-2" />
              Customer Report
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle aged debtors
              }}
            >
              <CreditCardIcon className="h-4 w-4 mr-2" />
              Aged Debtors
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle sales analysis
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Sales Analysis
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Customer
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={customers || []}
        searchPlaceholder="Search customers..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Customer"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateCustomer}
          onCancel={() => setShowCreateModal(false)}
          schema={customerSchema}
          submitLabel="Create Customer"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Customer"
        size="xl"
      >
        {selectedCustomer && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditCustomer}
            onCancel={() => setShowEditModal(false)}
            schema={customerSchema}
            submitLabel="Update Customer"
            defaultValues={{
              customer_code: selectedCustomer.customer_code,
              customer_name: selectedCustomer.customer_name,
              contact_person: selectedCustomer.contact_person,
              address_line1: selectedCustomer.address_line1,
              address_line2: selectedCustomer.address_line2,
              city: selectedCustomer.city,
              state: selectedCustomer.state,
              postal_code: selectedCustomer.postal_code,
              country: selectedCustomer.country,
              phone: selectedCustomer.phone,
              fax: selectedCustomer.fax,
              email: selectedCustomer.email,
              website: selectedCustomer.website,
              tax_number: selectedCustomer.tax_number,
              payment_terms: selectedCustomer.payment_terms,
              currency_code: selectedCustomer.currency_code,
              credit_limit: selectedCustomer.credit_limit.toString(),
              discount_percent: selectedCustomer.discount_percent.toString(),
              customer_type: selectedCustomer.customer_type,
              sales_rep: selectedCustomer.sales_rep,
              price_list: selectedCustomer.price_list,
              notes: selectedCustomer.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}