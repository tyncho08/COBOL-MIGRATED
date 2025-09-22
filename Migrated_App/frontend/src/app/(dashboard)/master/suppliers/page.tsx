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
  BuildingStorefrontIcon,
  DocumentTextIcon,
  CreditCardIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
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
  ytd_purchases: number
  is_active: boolean
  on_hold: boolean
  supplier_type: string
  account_number?: string
  bank_details?: string
  notes?: string
  created_date: string
  last_purchase_date?: string
}

// Schema
const supplierSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier code is required'),
  supplier_name: z.string().min(1, 'Supplier name is required'),
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
  supplier_type: z.string().min(1, 'Supplier type is required'),
  account_number: z.string().optional(),
  bank_details: z.string().optional(),
  notes: z.string().optional(),
})

// Mock data
const mockSuppliers: Supplier[] = [
  {
    id: 1,
    supplier_code: 'SUPP001',
    supplier_name: 'ABC Supplies Ltd',
    contact_person: 'John Smith',
    address_line1: '123 Business Street',
    address_line2: 'Industrial Estate',
    city: 'New York',
    state: 'NY',
    postal_code: '10001',
    country: 'USA',
    phone: '+1 555-0123',
    fax: '+1 555-0124',
    email: 'orders@abc-supplies.com',
    website: 'www.abc-supplies.com',
    tax_number: '12-3456789',
    payment_terms: '30 DAYS',
    currency_code: 'USD',
    credit_limit: 50000.00,
    balance: 15000.00,
    ytd_purchases: 125000.00,
    is_active: true,
    on_hold: false,
    supplier_type: 'TRADE',
    account_number: 'ABC-001',
    bank_details: 'Bank of America - 123456789',
    created_date: '2024-01-01',
    last_purchase_date: '2024-01-15',
  },
  {
    id: 2,
    supplier_code: 'SUPP002',
    supplier_name: 'Tech Components Inc',
    contact_person: 'Jane Doe',
    address_line1: '456 Technology Way',
    city: 'San Francisco',
    state: 'CA',
    postal_code: '94105',
    country: 'USA',
    phone: '+1 555-0456',
    email: 'purchasing@tech-components.com',
    website: 'www.tech-components.com',
    tax_number: '98-7654321',
    payment_terms: '60 DAYS',
    currency_code: 'USD',
    credit_limit: 75000.00,
    balance: 8500.00,
    ytd_purchases: 85000.00,
    is_active: true,
    on_hold: false,
    supplier_type: 'MANUFACTURER',
    account_number: 'TC-002',
    created_date: '2024-01-01',
    last_purchase_date: '2024-01-12',
  },
  {
    id: 3,
    supplier_code: 'SUPP003',
    supplier_name: 'Office Supplies Co',
    contact_person: 'Bob Johnson',
    address_line1: '789 Office Park',
    city: 'Chicago',
    state: 'IL',
    postal_code: '60601',
    country: 'USA',
    phone: '+1 555-0789',
    email: 'sales@office-supplies.com',
    tax_number: '55-9876543',
    payment_terms: '30 DAYS',
    currency_code: 'USD',
    credit_limit: 25000.00,
    balance: 3200.00,
    ytd_purchases: 45000.00,
    is_active: true,
    on_hold: true,
    supplier_type: 'TRADE',
    notes: 'Payment issues - on hold pending resolution',
    created_date: '2024-01-01',
    last_purchase_date: '2024-01-10',
  },
]

const getSupplierTypeBadge = (type: string) => {
  switch (type) {
    case 'TRADE':
      return <Badge variant="info">Trade</Badge>
    case 'MANUFACTURER':
      return <Badge variant="success">Manufacturer</Badge>
    case 'SERVICE':
      return <Badge variant="warning">Service</Badge>
    case 'UTILITIES':
      return <Badge variant="secondary">Utilities</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (isActive: boolean, onHold: boolean) => {
  if (onHold) {
    return <Badge variant="danger">On Hold</Badge>
  }
  if (isActive) {
    return <Badge variant="success">Active</Badge>
  }
  return <Badge variant="default">Inactive</Badge>
}

export default function SuppliersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)

  const { data: suppliers, isLoading } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => Promise.resolve(mockSuppliers),
  })

  const columns: ColumnDef<Supplier>[] = [
    {
      accessorKey: 'supplier_code',
      header: 'Supplier Code',
    },
    {
      accessorKey: 'supplier_name',
      header: 'Supplier Name',
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
        return (
          <span className={amount > 0 ? 'text-red-600' : amount < 0 ? 'text-green-600' : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(Math.abs(amount))}
            {amount < 0 && ' CR'}
          </span>
        )
      },
    },
    {
      accessorKey: 'ytd_purchases',
      header: 'YTD Purchases',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('ytd_purchases'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'supplier_type',
      header: 'Type',
      cell: ({ row }) => {
        return getSupplierTypeBadge(row.getValue('supplier_type'))
      },
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const supplier = row.original
        return getStatusBadge(supplier.is_active, supplier.on_hold)
      },
    },
    {
      accessorKey: 'last_purchase_date',
      header: 'Last Purchase',
      cell: ({ row }) => {
        const date = row.getValue('last_purchase_date') as string
        return date ? new Date(date).toLocaleDateString() : 'Never'
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const supplier = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedSupplier(supplier)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view supplier details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle supplier statement
              }}
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
            {supplier.email && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle email supplier
                }}
              >
                <EnvelopeIcon className="h-4 w-4" />
              </Button>
            )}
            {supplier.phone && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle call supplier
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
      name: 'supplier_code',
      label: 'Supplier Code',
      type: 'text',
      required: true,
    },
    {
      name: 'supplier_name',
      label: 'Supplier Name',
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
      name: 'supplier_type',
      label: 'Supplier Type',
      type: 'select',
      required: true,
      options: [
        { value: 'TRADE', label: 'Trade Supplier' },
        { value: 'MANUFACTURER', label: 'Manufacturer' },
        { value: 'SERVICE', label: 'Service Provider' },
        { value: 'UTILITIES', label: 'Utilities' },
      ],
    },
    {
      name: 'account_number',
      label: 'Account Number',
      type: 'text',
    },
    {
      name: 'bank_details',
      label: 'Bank Details',
      type: 'text',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateSupplier = (data: any) => {
    console.log('Creating supplier:', data)
    setShowCreateModal(false)
  }

  const handleEditSupplier = (data: any) => {
    console.log('Editing supplier:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Suppliers"
        description="Manage supplier information and relationships"
        breadcrumbs={[
          { label: 'Master Data', href: '/master' },
          { label: 'Suppliers' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle supplier report
              }}
            >
              <BuildingStorefrontIcon className="h-4 w-4 mr-2" />
              Supplier Report
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle aged creditors
              }}
            >
              <CreditCardIcon className="h-4 w-4 mr-2" />
              Aged Creditors
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Supplier
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={suppliers || []}
        searchPlaceholder="Search suppliers..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Supplier"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateSupplier}
          onCancel={() => setShowCreateModal(false)}
          schema={supplierSchema}
          submitLabel="Create Supplier"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Supplier"
        size="xl"
      >
        {selectedSupplier && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditSupplier}
            onCancel={() => setShowEditModal(false)}
            schema={supplierSchema}
            submitLabel="Update Supplier"
            defaultValues={{
              supplier_code: selectedSupplier.supplier_code,
              supplier_name: selectedSupplier.supplier_name,
              contact_person: selectedSupplier.contact_person,
              address_line1: selectedSupplier.address_line1,
              address_line2: selectedSupplier.address_line2,
              city: selectedSupplier.city,
              state: selectedSupplier.state,
              postal_code: selectedSupplier.postal_code,
              country: selectedSupplier.country,
              phone: selectedSupplier.phone,
              fax: selectedSupplier.fax,
              email: selectedSupplier.email,
              website: selectedSupplier.website,
              tax_number: selectedSupplier.tax_number,
              payment_terms: selectedSupplier.payment_terms,
              currency_code: selectedSupplier.currency_code,
              credit_limit: selectedSupplier.credit_limit.toString(),
              supplier_type: selectedSupplier.supplier_type,
              account_number: selectedSupplier.account_number,
              bank_details: selectedSupplier.bank_details,
              notes: selectedSupplier.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}