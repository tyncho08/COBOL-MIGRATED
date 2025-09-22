'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ColumnDef } from '@tanstack/react-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Modal } from '@/components/ui/modal'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
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
  ChartBarIcon,
  TrashIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { Customer, customersApi } from '@/lib/api/customers'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

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


const getCustomerTypeBadge = (type: string) => {
  switch (type) {
    case 'CORPORATE':
      return <Badge variant="info">Corporate</Badge>
    case 'BUSINESS':
      return <Badge variant="success">Business</Badge>
    case 'INDIVIDUAL':
      return <Badge variant="warning">Individual</Badge>
    case 'GOVERNMENT':
      return <Badge variant="default">Government</Badge>
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
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [customerToDelete, setCustomerToDelete] = useState<Customer | null>(null)

  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for customers
  const { data: customers, isLoading, error } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customersApi.getAll(),
  })

  // Mutation for creating customer
  const createMutation = useMutation({
    mutationFn: customersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      toast.success('Customer created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create customer')
    },
  })

  // Mutation for updating customer
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Customer> }) =>
      customersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      toast.success('Customer updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update customer')
    },
  })

  // Mutation for deleting customer
  const deleteMutation = useMutation({
    mutationFn: customersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      toast.success('Customer deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete customer')
    },
  })

  // Mutation for toggling hold status
  const toggleHoldMutation = useMutation({
    mutationFn: ({ id, onHold }: { id: number; onHold: boolean }) =>
      customersApi.toggleHold(id, onHold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      toast.success('Customer hold status updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update hold status')
    },
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
        return getStatusBadge(customer.is_active || true, customer.on_hold || false, customer.balance || 0, customer.credit_limit || 0)
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
                setSelectedCustomer(customer)
                setShowDetailsModal(true)
              }}
              title="View Details"
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await customersApi.getStatement(customer.id!)
                  toast.success('Statement generated')
                } catch (error) {
                  toast.error('Failed to generate statement')
                }
              }}
              title="Generate Statement"
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await customersApi.getSalesAnalysis(customer.id!)
                  toast.success('Sales analysis generated')
                } catch (error) {
                  toast.error('Failed to generate sales analysis')
                }
              }}
              title="Sales Analysis"
            >
              <ChartBarIcon className="h-4 w-4" />
            </Button>
            {canEdit('master') && (
              <Button
                size="sm"
                variant={customer.on_hold ? "secondary" : "outline"}
                onClick={() => handleToggleHold(customer)}
                title={customer.on_hold ? "Remove Hold" : "Place on Hold"}
              >
                {customer.on_hold ? "On Hold" : "Active"}
              </Button>
            )}
            {customer.email && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  window.location.href = `mailto:${customer.email}`
                }}
                title="Send Email"
              >
                <EnvelopeIcon className="h-4 w-4" />
              </Button>
            )}
            {customer.phone && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  window.location.href = `tel:${customer.phone}`
                }}
                title="Call Customer"
              >
                <PhoneIcon className="h-4 w-4" />
              </Button>
            )}
            {canDelete('master') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteCustomer(customer)}
                className="text-red-600 hover:text-red-700"
                title="Delete Customer"
              >
                <TrashIcon className="h-4 w-4" />
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
    const customerData = {
      ...data,
      credit_limit: parseFloat(data.credit_limit || '0'),
      discount_percent: parseFloat(data.discount_percent || '0'),
      is_active: true,
      on_hold: false,
    }
    createMutation.mutate(customerData)
  }

  const handleEditCustomer = (data: any) => {
    if (selectedCustomer?.id) {
      const customerData = {
        ...data,
        credit_limit: parseFloat(data.credit_limit || '0'),
        discount_percent: parseFloat(data.discount_percent || '0'),
      }
      updateMutation.mutate({ id: selectedCustomer.id, data: customerData })
    }
  }

  const handleDeleteCustomer = (customer: Customer) => {
    setCustomerToDelete(customer)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (customerToDelete?.id) {
      deleteMutation.mutate(customerToDelete.id)
      setShowDeleteDialog(false)
      setCustomerToDelete(null)
    }
  }

  const handleToggleHold = (customer: Customer) => {
    if (customer.id) {
      toggleHoldMutation.mutate({ id: customer.id, onHold: !customer.on_hold })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading customers...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load customers</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['customers'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
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
              onClick={async () => {
                try {
                  await customersApi.getReport()
                  toast.success('Customer report generated')
                } catch (error) {
                  toast.error('Failed to generate customer report')
                }
              }}
            >
              <UsersIcon className="h-4 w-4 mr-2" />
              Customer Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await customersApi.getAgedDebtors()
                  toast.success('Aged debtors report generated')
                } catch (error) {
                  toast.error('Failed to generate aged debtors report')
                }
              }}
            >
              <CreditCardIcon className="h-4 w-4 mr-2" />
              Aged Debtors
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await customersApi.getSalesAnalysisReport()
                  toast.success('Sales analysis report generated')
                } catch (error) {
                  toast.error('Failed to generate sales analysis report')
                }
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

      {/* Customer Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title={`Customer Details - ${selectedCustomer?.customer_code}`}
        size="xl"
      >
        {selectedCustomer && (
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Customer Code</label>
                <p className="mt-1 text-sm text-gray-900">{selectedCustomer.customer_code}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Customer Name</label>
                <p className="mt-1 text-sm text-gray-900">{selectedCustomer.customer_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Contact Person</label>
                <p className="mt-1 text-sm text-gray-900">{selectedCustomer.contact_person || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Customer Type</label>
                <p className="mt-1 text-sm text-gray-900">{selectedCustomer.customer_type}</p>
              </div>
            </div>

            {/* Address Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Address Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Address</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedCustomer.address_line1}
                    {selectedCustomer.address_line2 && <><br />{selectedCustomer.address_line2}</>}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">City, State</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedCustomer.city}{selectedCustomer.state && `, ${selectedCustomer.state}`}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Postal Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.postal_code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Country</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.country}</p>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Contact Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.phone || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.email || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Financial Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Financial Information</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Current Balance</label>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: selectedCustomer.currency_code || 'USD',
                    }).format(selectedCustomer.balance || 0)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Credit Limit</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedCustomer.credit_limit ? new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: selectedCustomer.currency_code || 'USD',
                    }).format(selectedCustomer.credit_limit) : 'No Limit'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Payment Terms</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.payment_terms}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Currency</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.currency_code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Discount %</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.discount_percent}%</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Sales Rep</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedCustomer.sales_rep || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Notes */}
            {selectedCustomer.notes && (
              <div className="border-t pt-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Notes</h3>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{selectedCustomer.notes}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="border-t pt-4 flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowDetailsModal(false)
                  setShowEditModal(true)
                }}
              >
                Edit Customer
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowDetailsModal(false)}
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setCustomerToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Customer"
        message={`Are you sure you want to delete ${customerToDelete?.customer_name}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}