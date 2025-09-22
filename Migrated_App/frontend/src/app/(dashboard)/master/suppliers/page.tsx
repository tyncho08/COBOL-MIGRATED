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
  BuildingStorefrontIcon,
  DocumentTextIcon,
  CreditCardIcon,
  ChartBarIcon,
  TrashIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { Supplier, suppliersApi } from '@/lib/api/suppliers'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

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
  bank_account: z.string().optional(),
  bank_name: z.string().optional(),
  bank_branch: z.string().optional(),
  swift_code: z.string().optional(),
  discount_percent: z.string().optional(),
  supplier_type: z.string().min(1, 'Supplier type is required'),
  category: z.string().optional(),
  notes: z.string().optional(),
})

const getSupplierTypeBadge = (type: string) => {
  switch (type) {
    case 'MANUFACTURER':
      return <Badge variant="info">Manufacturer</Badge>
    case 'DISTRIBUTOR':
      return <Badge variant="success">Distributor</Badge>
    case 'WHOLESALER':
      return <Badge variant="warning">Wholesaler</Badge>
    case 'SERVICE':
      return <Badge variant="default">Service</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (isActive: boolean, onHold: boolean) => {
  if (onHold) {
    return <Badge variant="danger">On Hold</Badge>
  }
  if (!isActive) {
    return <Badge variant="default">Inactive</Badge>
  }
  return <Badge variant="success">Active</Badge>
}

export default function SuppliersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null)
  const [supplierToDelete, setSupplierToDelete] = useState<Supplier | null>(null)

  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for suppliers
  const { data: suppliers, isLoading, error } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => suppliersApi.getAll(),
  })

  // Mutation for creating supplier
  const createMutation = useMutation({
    mutationFn: suppliersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success('Supplier created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create supplier')
    },
  })

  // Mutation for updating supplier
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Supplier> }) =>
      suppliersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success('Supplier updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update supplier')
    },
  })

  // Mutation for deleting supplier
  const deleteMutation = useMutation({
    mutationFn: suppliersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success('Supplier deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete supplier')
    },
  })

  // Mutation for toggling hold status
  const toggleHoldMutation = useMutation({
    mutationFn: ({ id, onHold }: { id: number; onHold: boolean }) =>
      suppliersApi.toggleHold(id, onHold),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      toast.success('Supplier hold status updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update hold status')
    },
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
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('balance') || '0')
        const isCredit = amount < 0
        
        return (
          <span className={
            isCredit ? 'text-red-600 font-bold' : 
            amount > 0 ? 'text-green-600' : ''
          }>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(Math.abs(amount))}
            {isCredit && ' DR'}
          </span>
        )
      },
    },
    {
      accessorKey: 'ytd_purchases',
      header: 'YTD Purchases',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('ytd_purchases') || '0')
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
        const percent = parseFloat(row.getValue('discount_percent') || '0')
        return `${percent.toFixed(1)}%`
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
        return getStatusBadge(supplier.is_active || true, supplier.on_hold || false)
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
                setSelectedSupplier(supplier)
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
                  await suppliersApi.getStatement(supplier.id!)
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
                  await suppliersApi.getPurchaseAnalysis(supplier.id!)
                  toast.success('Purchase analysis generated')
                } catch (error) {
                  toast.error('Failed to generate purchase analysis')
                }
              }}
              title="Purchase Analysis"
            >
              <ChartBarIcon className="h-4 w-4" />
            </Button>
            {canEdit('master') && (
              <Button
                size="sm"
                variant={supplier.on_hold ? "secondary" : "outline"}
                onClick={() => handleToggleHold(supplier)}
                title={supplier.on_hold ? "Remove Hold" : "Place on Hold"}
              >
                {supplier.on_hold ? "On Hold" : "Active"}
              </Button>
            )}
            {supplier.email && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  window.location.href = `mailto:${supplier.email}`
                }}
                title="Send Email"
              >
                <EnvelopeIcon className="h-4 w-4" />
              </Button>
            )}
            {supplier.phone && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  window.location.href = `tel:${supplier.phone}`
                }}
                title="Call Supplier"
              >
                <PhoneIcon className="h-4 w-4" />
              </Button>
            )}
            {canDelete('master') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteSupplier(supplier)}
                className="text-red-600 hover:text-red-700"
                title="Delete Supplier"
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
        { value: 'CHN', label: 'China' },
        { value: 'IND', label: 'India' },
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
        { value: '45 DAYS', label: '45 Days' },
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
        { value: 'CNY', label: 'Chinese Yuan' },
        { value: 'INR', label: 'Indian Rupee' },
      ],
    },
    {
      name: 'bank_account',
      label: 'Bank Account Number',
      type: 'text',
    },
    {
      name: 'bank_name',
      label: 'Bank Name',
      type: 'text',
    },
    {
      name: 'bank_branch',
      label: 'Bank Branch',
      type: 'text',
    },
    {
      name: 'swift_code',
      label: 'SWIFT Code',
      type: 'text',
    },
    {
      name: 'discount_percent',
      label: 'Discount Percentage',
      type: 'number',
    },
    {
      name: 'supplier_type',
      label: 'Supplier Type',
      type: 'select',
      required: true,
      options: [
        { value: 'MANUFACTURER', label: 'Manufacturer' },
        { value: 'DISTRIBUTOR', label: 'Distributor' },
        { value: 'WHOLESALER', label: 'Wholesaler' },
        { value: 'SERVICE', label: 'Service Provider' },
        { value: 'OTHER', label: 'Other' },
      ],
    },
    {
      name: 'category',
      label: 'Category',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'RAW_MATERIALS', label: 'Raw Materials' },
        { value: 'COMPONENTS', label: 'Components' },
        { value: 'FINISHED_GOODS', label: 'Finished Goods' },
        { value: 'SERVICES', label: 'Services' },
        { value: 'UTILITIES', label: 'Utilities' },
        { value: 'OTHER', label: 'Other' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateSupplier = (data: any) => {
    const supplierData = {
      ...data,
      discount_percent: parseFloat(data.discount_percent || '0'),
      is_active: true,
      on_hold: false,
    }
    createMutation.mutate(supplierData)
  }

  const handleEditSupplier = (data: any) => {
    if (selectedSupplier?.id) {
      const supplierData = {
        ...data,
        discount_percent: parseFloat(data.discount_percent || '0'),
      }
      updateMutation.mutate({ id: selectedSupplier.id, data: supplierData })
    }
  }

  const handleDeleteSupplier = (supplier: Supplier) => {
    setSupplierToDelete(supplier)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (supplierToDelete?.id) {
      deleteMutation.mutate(supplierToDelete.id)
      setShowDeleteDialog(false)
      setSupplierToDelete(null)
    }
  }

  const handleToggleHold = (supplier: Supplier) => {
    if (supplier.id) {
      toggleHoldMutation.mutate({ id: supplier.id, onHold: !supplier.on_hold })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading suppliers...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load suppliers</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['suppliers'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
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
              onClick={async () => {
                try {
                  await suppliersApi.getReport()
                  toast.success('Supplier report generated')
                } catch (error) {
                  toast.error('Failed to generate supplier report')
                }
              }}
            >
              <BuildingStorefrontIcon className="h-4 w-4 mr-2" />
              Supplier Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await suppliersApi.getAgedCreditors()
                  toast.success('Aged creditors report generated')
                } catch (error) {
                  toast.error('Failed to generate aged creditors report')
                }
              }}
            >
              <CreditCardIcon className="h-4 w-4 mr-2" />
              Aged Creditors
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await suppliersApi.getPurchaseAnalysisReport()
                  toast.success('Purchase analysis report generated')
                } catch (error) {
                  toast.error('Failed to generate purchase analysis report')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Purchase Analysis
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
          loading={createMutation.isPending}
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
            loading={updateMutation.isPending}
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
              bank_account: selectedSupplier.bank_account,
              bank_name: selectedSupplier.bank_name,
              bank_branch: selectedSupplier.bank_branch,
              swift_code: selectedSupplier.swift_code,
              discount_percent: selectedSupplier.discount_percent?.toString(),
              supplier_type: selectedSupplier.supplier_type,
              category: selectedSupplier.category,
              notes: selectedSupplier.notes,
            }}
          />
        )}
      </Modal>

      {/* Supplier Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title={`Supplier Details - ${selectedSupplier?.supplier_code}`}
        size="xl"
      >
        {selectedSupplier && (
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Supplier Code</label>
                <p className="mt-1 text-sm text-gray-900">{selectedSupplier.supplier_code}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Supplier Name</label>
                <p className="mt-1 text-sm text-gray-900">{selectedSupplier.supplier_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Contact Person</label>
                <p className="mt-1 text-sm text-gray-900">{selectedSupplier.contact_person || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Supplier Type</label>
                <p className="mt-1 text-sm text-gray-900">{selectedSupplier.supplier_type}</p>
              </div>
            </div>

            {/* Address Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Address Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Address</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedSupplier.address_line1}
                    {selectedSupplier.address_line2 && <><br />{selectedSupplier.address_line2}</>}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">City, State</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedSupplier.city}{selectedSupplier.state && `, ${selectedSupplier.state}`}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Postal Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.postal_code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Country</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.country}</p>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Contact Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.phone || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.email || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Fax</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.fax || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Website</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.website || 'N/A'}</p>
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
                      currency: selectedSupplier.currency_code || 'USD',
                    }).format(selectedSupplier.balance || 0)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">YTD Purchases</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: selectedSupplier.currency_code || 'USD',
                    }).format(selectedSupplier.ytd_purchases || 0)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Payment Terms</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.payment_terms}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Currency</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.currency_code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Discount %</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.discount_percent || 0}%</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tax Number</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.tax_number || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Banking Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Banking Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Bank Name</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.bank_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Bank Branch</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.bank_branch || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Account Number</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.bank_account || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">SWIFT Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.swift_code || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Additional Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Additional Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Category</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedSupplier.category || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Purchase Date</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedSupplier.last_purchase_date ? new Date(selectedSupplier.last_purchase_date).toLocaleDateString() : 'Never'}
                  </p>
                </div>
              </div>
            </div>

            {/* Notes */}
            {selectedSupplier.notes && (
              <div className="border-t pt-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Notes</h3>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{selectedSupplier.notes}</p>
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
                Edit Supplier
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
          setSupplierToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Supplier"
        message={`Are you sure you want to delete ${supplierToDelete?.supplier_name}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}