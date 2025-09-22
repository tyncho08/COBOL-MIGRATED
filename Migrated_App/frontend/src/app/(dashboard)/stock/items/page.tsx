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
import { PlusIcon, EyeIcon, PencilIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface StockItem {
  id: number
  stock_code: string
  description: string
  category_code?: string
  unit_of_measure: string
  location?: string
  quantity_on_hand: number
  sell_price?: number
  unit_cost?: number
  vat_code: string
  reorder_point?: number
  is_active: boolean
}

// Schema
const stockItemSchema = z.object({
  stock_code: z.string().min(1, 'Stock code is required'),
  description: z.string().min(1, 'Description is required'),
  category_code: z.string().optional(),
  unit_of_measure: z.string().min(1, 'Unit of measure is required'),
  location: z.string().optional(),
  sell_price: z.string().optional(),
  unit_cost: z.string().optional(),
  vat_code: z.string().min(1, 'VAT code is required'),
  supplier_code: z.string().optional(),
  reorder_point: z.string().optional(),
  economic_order_qty: z.string().optional(),
})

// Mock data
const mockStockItems: StockItem[] = [
  {
    id: 1,
    stock_code: 'CPU001',
    description: 'Intel Core i7 Processor',
    category_code: 'COMP',
    unit_of_measure: 'EACH',
    location: 'MAIN',
    quantity_on_hand: 25,
    sell_price: 399.99,
    unit_cost: 299.99,
    vat_code: 'S',
    reorder_point: 10,
    is_active: true,
  },
  {
    id: 2,
    stock_code: 'RAM001',
    description: '16GB DDR4 Memory',
    category_code: 'COMP',
    unit_of_measure: 'EACH',
    location: 'MAIN',
    quantity_on_hand: 5,
    sell_price: 79.99,
    unit_cost: 59.99,
    vat_code: 'S',
    reorder_point: 10,
    is_active: true,
  },
  {
    id: 3,
    stock_code: 'HDD001',
    description: '1TB SSD Drive',
    category_code: 'COMP',
    unit_of_measure: 'EACH',
    location: 'MAIN',
    quantity_on_hand: 50,
    sell_price: 129.99,
    unit_cost: 99.99,
    vat_code: 'S',
    reorder_point: 20,
    is_active: true,
  },
]

const getStockStatus = (item: StockItem) => {
  if (item.quantity_on_hand <= 0) {
    return <Badge variant="danger">Out of Stock</Badge>
  }
  if (item.reorder_point && item.quantity_on_hand <= item.reorder_point) {
    return <Badge variant="warning">Low Stock</Badge>
  }
  return <Badge variant="success">In Stock</Badge>
}

export default function StockItemsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null)

  const { data: stockItems, isLoading } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => Promise.resolve(mockStockItems),
  })

  const columns: ColumnDef<StockItem>[] = [
    {
      accessorKey: 'stock_code',
      header: 'Stock Code',
    },
    {
      accessorKey: 'description',
      header: 'Description',
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
    },
    {
      accessorKey: 'quantity_on_hand',
      header: 'Qty on Hand',
      cell: ({ row }) => {
        const item = row.original
        const qty = row.getValue('quantity_on_hand') as number
        const isLowStock = item.reorder_point && qty <= item.reorder_point
        
        return (
          <div className="flex items-center space-x-2">
            <span>{qty}</span>
            {isLowStock && (
              <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'sell_price',
      header: 'Sell Price',
      cell: ({ row }) => {
        const price = row.getValue('sell_price') as number
        return price ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(price) : '-'
      },
    },
    {
      accessorKey: 'unit_cost',
      header: 'Unit Cost',
      cell: ({ row }) => {
        const cost = row.getValue('unit_cost') as number
        return cost ? new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(cost) : '-'
      },
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        return getStockStatus(row.original)
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
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view item details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
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
      name: 'category_code',
      label: 'Category',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'COMP', label: 'Computer Components' },
        { value: 'PERI', label: 'Peripherals' },
        { value: 'SOFT', label: 'Software' },
        { value: 'CONS', label: 'Consumables' },
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
        { value: 'METER', label: 'Meter' },
      ],
    },
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'MAIN', label: 'Main Warehouse' },
        { value: 'SHOP', label: 'Shop Floor' },
        { value: 'OFF', label: 'Office' },
      ],
    },
    {
      name: 'sell_price',
      label: 'Sell Price',
      type: 'number',
    },
    {
      name: 'unit_cost',
      label: 'Unit Cost',
      type: 'number',
    },
    {
      name: 'vat_code',
      label: 'VAT Code',
      type: 'select',
      required: true,
      options: [
        { value: 'S', label: 'Standard Rate' },
        { value: 'Z', label: 'Zero Rate' },
        { value: 'E', label: 'Exempt' },
      ],
    },
    {
      name: 'supplier_code',
      label: 'Primary Supplier',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'SUP001', label: 'Supplier 001' },
        { value: 'SUP002', label: 'Supplier 002' },
        { value: 'SUP003', label: 'Supplier 003' },
      ],
    },
    {
      name: 'reorder_point',
      label: 'Reorder Point',
      type: 'number',
    },
    {
      name: 'economic_order_qty',
      label: 'Economic Order Qty',
      type: 'number',
    },
  ]

  const handleCreateItem = (data: any) => {
    console.log('Creating stock item:', data)
    setShowCreateModal(false)
  }

  const handleEditItem = (data: any) => {
    console.log('Editing stock item:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Stock Items"
        description="Manage your inventory items and stock levels"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Items' },
        ]}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Stock Item
          </Button>
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
          submitLabel="Create Item"
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
            submitLabel="Update Item"
            defaultValues={{
              stock_code: selectedItem.stock_code,
              description: selectedItem.description,
              category_code: selectedItem.category_code,
              unit_of_measure: selectedItem.unit_of_measure,
              location: selectedItem.location,
              sell_price: selectedItem.sell_price?.toString(),
              unit_cost: selectedItem.unit_cost?.toString(),
              vat_code: selectedItem.vat_code,
              reorder_point: selectedItem.reorder_point?.toString(),
            }}
          />
        )}
      </Modal>
    </div>
  )
}