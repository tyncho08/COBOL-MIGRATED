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
  ExclamationTriangleIcon,
  ArrowsRightLeftIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  TrashIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { StockItem, StockMovement, stockItemsApi } from '@/lib/api/stock-items'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

// Schema
const stockItemSchema = z.object({
  stock_code: z.string().min(1, 'Stock code is required'),
  description: z.string().min(1, 'Description is required'),
  long_description: z.string().optional(),
  category_code: z.string().optional(),
  unit_of_measure: z.string().min(1, 'Unit of measure is required'),
  location: z.string().optional(),
  bin_location: z.string().optional(),
  reorder_level: z.string().optional(),
  reorder_quantity: z.string().optional(),
  minimum_quantity: z.string().optional(),
  maximum_quantity: z.string().optional(),
  lead_time_days: z.string().optional(),
  unit_cost: z.string().min(1, 'Unit cost is required'),
  selling_price: z.string().min(1, 'Selling price is required'),
  vat_code: z.string().min(1, 'VAT code is required'),
  barcode: z.string().optional(),
  supplier_code: z.string().optional(),
  manufacturer_code: z.string().optional(),
  manufacturer_part_no: z.string().optional(),
  weight: z.string().optional(),
  dimensions: z.string().optional(),
  is_service_item: z.boolean().optional(),
  allow_negative_stock: z.boolean().optional(),
  track_serial_numbers: z.boolean().optional(),
  track_batch_numbers: z.boolean().optional(),
  notes: z.string().optional(),
})

// Schema for stock adjustment
const stockAdjustmentSchema = z.object({
  adjustment_type: z.enum(['INCREASE', 'DECREASE', 'SET']),
  quantity: z.string().min(1, 'Quantity is required'),
  reason: z.string().min(1, 'Reason is required'),
  reference: z.string().optional(),
  cost: z.string().optional(),
  location: z.string().optional(),
})

const getStockStatusBadge = (item: StockItem) => {
  const available = item.quantity_on_hand - (item.quantity_allocated || 0)
  
  if (item.quantity_on_hand === 0) {
    return <Badge variant="danger">Out of Stock</Badge>
  }
  if (item.quantity_on_hand < item.reorder_level) {
    return <Badge variant="warning">Low Stock</Badge>
  }
  if (available <= 0) {
    return <Badge variant="warning">All Allocated</Badge>
  }
  return <Badge variant="success">In Stock</Badge>
}

export default function StockItemsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showAdjustmentModal, setShowAdjustmentModal] = useState(false)
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showMovementsModal, setShowMovementsModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null)
  const [itemToDelete, setItemToDelete] = useState<StockItem | null>(null)

  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for stock items
  const { data: stockItems, isLoading, error } = useQuery({
    queryKey: ['stockItems'],
    queryFn: () => stockItemsApi.getAll(),
  })

  // Query for stock movements
  const { data: stockMovements } = useQuery({
    queryKey: ['stockMovements', selectedItem?.id],
    queryFn: () => selectedItem?.id ? stockItemsApi.getMovements(selectedItem.id) : null,
    enabled: !!selectedItem?.id && showMovementsModal,
  })

  // Mutation for creating stock item
  const createMutation = useMutation({
    mutationFn: stockItemsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockItems'] })
      toast.success('Stock item created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create stock item')
    },
  })

  // Mutation for updating stock item
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<StockItem> }) =>
      stockItemsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockItems'] })
      toast.success('Stock item updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update stock item')
    },
  })

  // Mutation for deleting stock item
  const deleteMutation = useMutation({
    mutationFn: stockItemsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockItems'] })
      toast.success('Stock item deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete stock item')
    },
  })

  // Mutation for adjusting stock
  const adjustStockMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      stockItemsApi.adjustStock(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockItems'] })
      toast.success('Stock adjusted successfully')
      setShowAdjustmentModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to adjust stock')
    },
  })

  const columns: ColumnDef<StockItem>[] = [
    {
      accessorKey: 'stock_code',
      header: 'Stock Code',
    },
    {
      accessorKey: 'description',
      header: 'Description',
      cell: ({ row }) => {
        const item = row.original
        return (
          <div>
            <div className="font-medium">{item.description}</div>
            {item.long_description && (
              <div className="text-sm text-gray-500">{item.long_description}</div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'category_code',
      header: 'Category',
    },
    {
      accessorKey: 'unit_of_measure',
      header: 'UOM',
    },
    {
      accessorKey: 'location',
      header: 'Location',
      cell: ({ row }) => {
        const item = row.original
        return (
          <div>
            <div>{item.location || '-'}</div>
            {item.bin_location && (
              <div className="text-sm text-gray-500">Bin: {item.bin_location}</div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'quantity_on_hand',
      header: 'On Hand',
      cell: ({ row }) => {
        const qty = row.getValue('quantity_on_hand') as number
        return (
          <span className={qty <= 0 ? 'text-red-600 font-bold' : ''}>
            {qty.toFixed(2)}
          </span>
        )
      },
    },
    {
      accessorKey: 'quantity_allocated',
      header: 'Allocated',
      cell: ({ row }) => {
        const qty = row.getValue('quantity_allocated') as number || 0
        return qty > 0 ? qty.toFixed(2) : '-'
      },
    },
    {
      accessorKey: 'quantity_available',
      header: 'Available',
      cell: ({ row }) => {
        const item = row.original
        const available = item.quantity_on_hand - (item.quantity_allocated || 0)
        return (
          <span className={available <= 0 ? 'text-red-600 font-bold' : 'text-green-600'}>
            {available.toFixed(2)}
          </span>
        )
      },
    },
    {
      accessorKey: 'reorder_level',
      header: 'Reorder Level',
      cell: ({ row }) => {
        const level = row.getValue('reorder_level') as number
        return level > 0 ? level.toFixed(2) : '-'
      },
    },
    {
      accessorKey: 'unit_cost',
      header: 'Unit Cost',
      cell: ({ row }) => {
        const cost = parseFloat(row.getValue('unit_cost') || '0')
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(cost)
      },
    },
    {
      accessorKey: 'selling_price',
      header: 'Selling Price',
      cell: ({ row }) => {
        const price = parseFloat(row.getValue('selling_price') || '0')
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(price)
      },
    },
    {
      accessorKey: 'vat_code',
      header: 'VAT Code',
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const item = row.original
        return getStockStatusBadge(item)
      },
    },
    {
      accessorKey: 'is_active',
      header: 'Active',
      cell: ({ row }) => {
        const isActive = row.getValue('is_active')
        return isActive ? (
          <Badge variant="success">Active</Badge>
        ) : (
          <Badge variant="default">Inactive</Badge>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const item = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedItem(item)
                setShowEditModal(true)
              }}
              title="Edit"
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedItem(item)
                setShowDetailsModal(true)
              }}
              title="View Details"
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            {canEdit('stock') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedItem(item)
                  setShowAdjustmentModal(true)
                }}
                title="Adjust Stock"
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedItem(item)
                setShowMovementsModal(true)
              }}
              title="View Movements"
            >
              <ArrowsRightLeftIcon className="h-4 w-4" />
            </Button>
            {item.quantity_on_hand < item.reorder_level && (
              <Button
                size="sm"
                variant="secondary"
                title="Below Reorder Level"
              >
                <ExclamationTriangleIcon className="h-4 w-4" />
              </Button>
            )}
            {canDelete('stock') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteItem(item)}
                className="text-red-600 hover:text-red-700"
                title="Delete"
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
      name: 'stock_code',
      label: 'Stock Code',
      type: 'text',
      required: true,
    },
    {
      name: 'description',
      label: 'Description',
      type: 'text',
      required: true,
    },
    {
      name: 'long_description',
      label: 'Long Description',
      type: 'textarea',
    },
    {
      name: 'category_code',
      label: 'Category',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'HARDWARE', label: 'Hardware' },
        { value: 'SOFTWARE', label: 'Software' },
        { value: 'ACCESSORIES', label: 'Accessories' },
        { value: 'CONSUMABLES', label: 'Consumables' },
        { value: 'SERVICES', label: 'Services' },
      ],
    },
    {
      name: 'unit_of_measure',
      label: 'Unit of Measure',
      type: 'select',
      required: true,
      options: [
        { value: 'EACH', label: 'Each' },
        { value: 'BOX', label: 'Box' },
        { value: 'PACK', label: 'Pack' },
        { value: 'KG', label: 'Kilogram' },
        { value: 'LITRE', label: 'Litre' },
        { value: 'METRE', label: 'Metre' },
        { value: 'HOUR', label: 'Hour' },
      ],
    },
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'MAIN', label: 'Main Warehouse' },
        { value: 'STORE1', label: 'Store 1' },
        { value: 'STORE2', label: 'Store 2' },
      ],
    },
    {
      name: 'bin_location',
      label: 'Bin Location',
      type: 'text',
    },
    {
      name: 'reorder_level',
      label: 'Reorder Level',
      type: 'number',
    },
    {
      name: 'reorder_quantity',
      label: 'Reorder Quantity',
      type: 'number',
    },
    {
      name: 'minimum_quantity',
      label: 'Minimum Quantity',
      type: 'number',
    },
    {
      name: 'maximum_quantity',
      label: 'Maximum Quantity',
      type: 'number',
    },
    {
      name: 'lead_time_days',
      label: 'Lead Time (Days)',
      type: 'number',
    },
    {
      name: 'unit_cost',
      label: 'Unit Cost',
      type: 'number',
      required: true,
    },
    {
      name: 'selling_price',
      label: 'Selling Price',
      type: 'number',
      required: true,
    },
    {
      name: 'vat_code',
      label: 'VAT Code',
      type: 'select',
      required: true,
      options: [
        { value: 'S', label: 'Standard Rate (20%)' },
        { value: 'R', label: 'Reduced Rate (5%)' },
        { value: 'Z', label: 'Zero Rated (0%)' },
        { value: 'E', label: 'Exempt' },
      ],
    },
    {
      name: 'barcode',
      label: 'Barcode',
      type: 'text',
    },
    {
      name: 'supplier_code',
      label: 'Default Supplier',
      type: 'text',
    },
    {
      name: 'manufacturer_code',
      label: 'Manufacturer Code',
      type: 'text',
    },
    {
      name: 'manufacturer_part_no',
      label: 'Manufacturer Part No',
      type: 'text',
    },
    {
      name: 'weight',
      label: 'Weight (kg)',
      type: 'number',
    },
    {
      name: 'dimensions',
      label: 'Dimensions',
      type: 'text',
    },
    {
      name: 'is_service_item',
      label: 'Service Item',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'allow_negative_stock',
      label: 'Allow Negative Stock',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'track_serial_numbers',
      label: 'Track Serial Numbers',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'track_batch_numbers',
      label: 'Track Batch Numbers',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const adjustmentFormFields: FormField[] = [
    {
      name: 'adjustment_type',
      label: 'Adjustment Type',
      type: 'select',
      required: true,
      options: [
        { value: 'INCREASE', label: 'Increase Stock' },
        { value: 'DECREASE', label: 'Decrease Stock' },
        { value: 'SET', label: 'Set Stock Level' },
      ],
    },
    {
      name: 'quantity',
      label: 'Quantity',
      type: 'number',
      required: true,
    },
    {
      name: 'reason',
      label: 'Reason',
      type: 'select',
      required: true,
      options: [
        { value: 'STOCK_TAKE', label: 'Stock Take' },
        { value: 'DAMAGED', label: 'Damaged Goods' },
        { value: 'LOST', label: 'Lost/Misplaced' },
        { value: 'FOUND', label: 'Found' },
        { value: 'CORRECTION', label: 'Correction' },
        { value: 'OTHER', label: 'Other' },
      ],
    },
    {
      name: 'reference',
      label: 'Reference',
      type: 'text',
    },
    {
      name: 'cost',
      label: 'Cost per Unit',
      type: 'number',
    },
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      options: [
        { value: '', label: 'Default' },
        { value: 'MAIN', label: 'Main Warehouse' },
        { value: 'STORE1', label: 'Store 1' },
        { value: 'STORE2', label: 'Store 2' },
      ],
    },
  ]

  const handleCreateItem = (data: any) => {
    const itemData = {
      ...data,
      reorder_level: parseFloat(data.reorder_level || '0'),
      reorder_quantity: parseFloat(data.reorder_quantity || '0'),
      minimum_quantity: parseFloat(data.minimum_quantity || '0'),
      maximum_quantity: parseFloat(data.maximum_quantity || '0'),
      lead_time_days: parseInt(data.lead_time_days || '0'),
      unit_cost: parseFloat(data.unit_cost),
      selling_price: parseFloat(data.selling_price),
      weight: parseFloat(data.weight || '0'),
      is_active: true,
      is_service_item: data.is_service_item === 'true',
      allow_negative_stock: data.allow_negative_stock === 'true',
      track_serial_numbers: data.track_serial_numbers === 'true',
      track_batch_numbers: data.track_batch_numbers === 'true',
    }
    createMutation.mutate(itemData)
  }

  const handleEditItem = (data: any) => {
    if (selectedItem?.id) {
      const itemData = {
        ...data,
        reorder_level: parseFloat(data.reorder_level || '0'),
        reorder_quantity: parseFloat(data.reorder_quantity || '0'),
        minimum_quantity: parseFloat(data.minimum_quantity || '0'),
        maximum_quantity: parseFloat(data.maximum_quantity || '0'),
        lead_time_days: parseInt(data.lead_time_days || '0'),
        unit_cost: parseFloat(data.unit_cost),
        selling_price: parseFloat(data.selling_price),
        weight: parseFloat(data.weight || '0'),
        is_service_item: data.is_service_item === 'true',
        allow_negative_stock: data.allow_negative_stock === 'true',
        track_serial_numbers: data.track_serial_numbers === 'true',
        track_batch_numbers: data.track_batch_numbers === 'true',
      }
      updateMutation.mutate({ id: selectedItem.id, data: itemData })
    }
  }

  const handleDeleteItem = (item: StockItem) => {
    setItemToDelete(item)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (itemToDelete?.id) {
      deleteMutation.mutate(itemToDelete.id)
      setShowDeleteDialog(false)
      setItemToDelete(null)
    }
  }

  const handleAdjustStock = (data: any) => {
    if (selectedItem?.id) {
      const adjustmentData = {
        ...data,
        quantity: parseFloat(data.quantity),
        cost: data.cost ? parseFloat(data.cost) : undefined,
      }
      adjustStockMutation.mutate({ id: selectedItem.id, data: adjustmentData })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading stock items...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load stock items</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['stockItems'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Stock Items"
        description="Manage inventory items and stock levels"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Items' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await stockItemsApi.getReorderReport()
                  toast.success('Reorder report generated')
                } catch (error) {
                  toast.error('Failed to generate reorder report')
                }
              }}
            >
              <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
              Reorder Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await stockItemsApi.getValuation()
                  toast.success('Stock valuation report generated')
                } catch (error) {
                  toast.error('Failed to generate valuation report')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Stock Valuation
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const blob = await stockItemsApi.export('excel')
                  // Handle blob download
                  toast.success('Stock items exported')
                } catch (error) {
                  toast.error('Failed to export stock items')
                }
              }}
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Stock Item
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={stockItems || []}
        searchPlaceholder="Search stock items..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Stock Item"
        size="xl"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateItem}
          onCancel={() => setShowCreateModal(false)}
          schema={stockItemSchema}
          submitLabel="Create Stock Item"
          loading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Stock Item"
        size="xl"
      >
        {selectedItem && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditItem}
            onCancel={() => setShowEditModal(false)}
            schema={stockItemSchema}
            submitLabel="Update Stock Item"
            loading={updateMutation.isPending}
            defaultValues={{
              stock_code: selectedItem.stock_code,
              description: selectedItem.description,
              long_description: selectedItem.long_description,
              category_code: selectedItem.category_code,
              unit_of_measure: selectedItem.unit_of_measure,
              location: selectedItem.location,
              bin_location: selectedItem.bin_location,
              reorder_level: selectedItem.reorder_level?.toString(),
              reorder_quantity: selectedItem.reorder_quantity?.toString(),
              minimum_quantity: selectedItem.minimum_quantity?.toString(),
              maximum_quantity: selectedItem.maximum_quantity?.toString(),
              lead_time_days: selectedItem.lead_time_days?.toString(),
              unit_cost: selectedItem.unit_cost.toString(),
              selling_price: selectedItem.selling_price.toString(),
              vat_code: selectedItem.vat_code,
              barcode: selectedItem.barcode,
              supplier_code: selectedItem.supplier_code,
              manufacturer_code: selectedItem.manufacturer_code,
              manufacturer_part_no: selectedItem.manufacturer_part_no,
              weight: selectedItem.weight?.toString(),
              dimensions: selectedItem.dimensions,
              is_service_item: selectedItem.is_service_item ? 'true' : 'false',
              allow_negative_stock: selectedItem.allow_negative_stock ? 'true' : 'false',
              track_serial_numbers: selectedItem.track_serial_numbers ? 'true' : 'false',
              track_batch_numbers: selectedItem.track_batch_numbers ? 'true' : 'false',
              notes: selectedItem.notes,
            }}
          />
        )}
      </Modal>

      {/* Stock Item Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title={`Stock Item Details - ${selectedItem?.stock_code}`}
        size="xl"
      >
        {selectedItem && (
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Stock Code</label>
                <p className="mt-1 text-sm text-gray-900">{selectedItem.stock_code}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="mt-1 text-sm text-gray-900">{selectedItem.description}</p>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700">Long Description</label>
                <p className="mt-1 text-sm text-gray-900">{selectedItem.long_description || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <p className="mt-1 text-sm text-gray-900">{selectedItem.category_code || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Unit of Measure</label>
                <p className="mt-1 text-sm text-gray-900">{selectedItem.unit_of_measure}</p>
              </div>
            </div>

            {/* Stock Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Stock Information</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Quantity on Hand</label>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {selectedItem.quantity_on_hand.toFixed(2)} {selectedItem.unit_of_measure}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Quantity Allocated</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {(selectedItem.quantity_allocated || 0).toFixed(2)} {selectedItem.unit_of_measure}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Available Quantity</label>
                  <p className="mt-1 text-sm font-medium text-green-600">
                    {(selectedItem.quantity_on_hand - (selectedItem.quantity_allocated || 0)).toFixed(2)} {selectedItem.unit_of_measure}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reorder Level</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.reorder_level ? `${selectedItem.reorder_level.toFixed(2)} ${selectedItem.unit_of_measure}` : 'Not Set'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Reorder Quantity</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.reorder_quantity ? `${selectedItem.reorder_quantity.toFixed(2)} ${selectedItem.unit_of_measure}` : 'Not Set'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Stock Status</label>
                  <div className="mt-1">{getStockStatusBadge(selectedItem)}</div>
                </div>
              </div>
            </div>

            {/* Location Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Location Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Location</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.location || 'Default'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Bin Location</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.bin_location || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Pricing Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Pricing Information</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Unit Cost</label>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedItem.unit_cost)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Selling Price</label>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedItem.selling_price)}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Margin</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {((selectedItem.selling_price - selectedItem.unit_cost) / selectedItem.selling_price * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">VAT Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.vat_code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Stock Value</label>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedItem.quantity_on_hand * selectedItem.unit_cost)}
                  </p>
                </div>
              </div>
            </div>

            {/* Supplier & Manufacturing Information */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Supplier & Manufacturing</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Default Supplier</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.supplier_code || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Lead Time</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.lead_time_days ? `${selectedItem.lead_time_days} days` : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Manufacturer Code</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.manufacturer_code || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Manufacturer Part No</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.manufacturer_part_no || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Physical Properties */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Physical Properties</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Weight</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.weight ? `${selectedItem.weight} kg` : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Dimensions</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.dimensions || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Barcode</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedItem.barcode || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Settings */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Service Item</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.is_service_item ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Allow Negative Stock</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.allow_negative_stock ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Track Serial Numbers</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.track_serial_numbers ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Track Batch Numbers</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.track_batch_numbers ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedItem.is_active ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Badge variant="default">Inactive</Badge>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Notes */}
            {selectedItem.notes && (
              <div className="border-t pt-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Notes</h3>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{selectedItem.notes}</p>
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
                Edit Item
              </Button>
              {canEdit('stock') && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDetailsModal(false)
                    setShowAdjustmentModal(true)
                  }}
                >
                  Adjust Stock
                </Button>
              )}
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

      {/* Stock Adjustment Modal */}
      <Modal
        isOpen={showAdjustmentModal}
        onClose={() => setShowAdjustmentModal(false)}
        title={`Adjust Stock - ${selectedItem?.stock_code}`}
        size="lg"
      >
        {selectedItem && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-sm text-gray-700">Current Stock Information</h4>
            <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Item:</span> {selectedItem.description}
              </div>
              <div>
                <span className="text-gray-500">Current Stock:</span> {selectedItem.quantity_on_hand}
              </div>
              <div>
                <span className="text-gray-500">Location:</span> {selectedItem.location || 'Default'}
              </div>
              <div>
                <span className="text-gray-500">Unit Cost:</span> ${selectedItem.unit_cost.toFixed(2)}
              </div>
            </div>
          </div>
        )}
        <FormBuilder
          fields={adjustmentFormFields}
          onSubmit={handleAdjustStock}
          onCancel={() => setShowAdjustmentModal(false)}
          schema={stockAdjustmentSchema}
          submitLabel="Adjust Stock"
          loading={adjustStockMutation.isPending}
        />
      </Modal>

      {/* Stock Movements Modal */}
      <Modal
        isOpen={showMovementsModal}
        onClose={() => setShowMovementsModal(false)}
        title={`Stock Movements - ${selectedItem?.stock_code}`}
        size="xl"
      >
        {selectedItem && (
          <div className="space-y-4">
            {/* Item Summary */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Current Stock Information</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Item:</span> {selectedItem.description}
                </div>
                <div>
                  <span className="text-gray-500">Current Stock:</span> {selectedItem.quantity_on_hand} {selectedItem.unit_of_measure}
                </div>
                <div>
                  <span className="text-gray-500">Location:</span> {selectedItem.location || 'Default'}
                </div>
              </div>
            </div>

            {/* Movements Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document Ref
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {stockMovements && stockMovements.length > 0 ? (
                    stockMovements.map((movement) => (
                      <tr key={movement.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(movement.movement_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <Badge 
                            variant={
                              movement.movement_type === 'IN' ? 'success' :
                              movement.movement_type === 'OUT' ? 'danger' :
                              movement.movement_type === 'ADJUST' ? 'warning' :
                              'default'
                            }
                          >
                            {movement.movement_type}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {movement.document_ref || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <span className={
                            movement.quantity > 0 ? 'text-green-600' : 'text-red-600'
                          }>
                            {movement.quantity > 0 ? '+' : ''}{movement.quantity.toFixed(2)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {movement.unit_cost ? new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD',
                          }).format(movement.unit_cost) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {movement.location || 'Default'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {movement.notes || '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                        No movements found for this item
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowMovementsModal(false)}
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
          setItemToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Stock Item"
        message={`Are you sure you want to delete ${itemToDelete?.stock_code} - ${itemToDelete?.description}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}