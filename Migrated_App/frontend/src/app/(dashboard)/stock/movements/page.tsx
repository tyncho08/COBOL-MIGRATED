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
  ArrowUpIcon, 
  ArrowDownIcon,
  ArrowsRightLeftIcon,
  DocumentTextIcon,
  ChartBarIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface StockMovement {
  id: number
  movement_number: string
  movement_date: string
  movement_type: string
  stock_id: number
  stock_code: string
  description: string
  quantity_moved: number
  unit_cost: number
  total_value: number
  quantity_before: number
  quantity_after: number
  reference?: string
  document_number?: string
  document_type?: string
  location_from?: string
  location_to?: string
  reason_code?: string
  reason_description?: string
  created_by: string
  notes?: string
}

// Schema
const stockMovementSchema = z.object({
  movement_type: z.string().min(1, 'Movement type is required'),
  stock_code: z.string().min(1, 'Stock code is required'),
  quantity_moved: z.string().min(1, 'Quantity is required'),
  unit_cost: z.string().optional(),
  reference: z.string().optional(),
  location_from: z.string().optional(),
  location_to: z.string().optional(),
  reason_code: z.string().optional(),
  reason_description: z.string().optional(),
  notes: z.string().optional(),
})

// Mock data
const mockStockMovements: StockMovement[] = [
  {
    id: 1,
    movement_number: 'SM001234',
    movement_date: '2024-01-15',
    movement_type: 'RECEIPT',
    stock_id: 1,
    stock_code: 'ITEM001',
    description: 'Computer Mouse - Optical',
    quantity_moved: 50,
    unit_cost: 15.00,
    total_value: 750.00,
    quantity_before: 100,
    quantity_after: 150,
    reference: 'GR001234',
    document_number: 'PO001234',
    document_type: 'PURCHASE_ORDER',
    location_to: 'WAREHOUSE-A',
    reason_code: 'PURCHASE',
    reason_description: 'Goods received from supplier',
    created_by: 'John Smith',
  },
  {
    id: 2,
    movement_number: 'SM001235',
    movement_date: '2024-01-16',
    movement_type: 'ISSUE',
    stock_id: 1,
    stock_code: 'ITEM001',
    description: 'Computer Mouse - Optical',
    quantity_moved: -25,
    unit_cost: 15.00,
    total_value: -375.00,
    quantity_before: 150,
    quantity_after: 125,
    reference: 'SO001234',
    document_number: 'SO001234',
    document_type: 'SALES_ORDER',
    location_from: 'WAREHOUSE-A',
    reason_code: 'SALE',
    reason_description: 'Issued for sales order',
    created_by: 'Jane Doe',
  },
  {
    id: 3,
    movement_number: 'SM001236',
    movement_date: '2024-01-17',
    movement_type: 'ADJUSTMENT',
    stock_id: 2,
    stock_code: 'ITEM002',
    description: 'Keyboard - Mechanical',
    quantity_moved: -2,
    unit_cost: 75.00,
    total_value: -150.00,
    quantity_before: 30,
    quantity_after: 28,
    reason_code: 'DAMAGE',
    reason_description: 'Damaged goods adjustment',
    created_by: 'Bob Johnson',
    notes: 'Items damaged during inspection',
  },
  {
    id: 4,
    movement_number: 'SM001237',
    movement_date: '2024-01-18',
    movement_type: 'TRANSFER',
    stock_id: 3,
    stock_code: 'ITEM003',
    description: 'Monitor - 24" LCD',
    quantity_moved: 10,
    unit_cost: 200.00,
    total_value: 2000.00,
    quantity_before: 20,
    quantity_after: 20, // Same total, just moved between locations
    location_from: 'WAREHOUSE-A',
    location_to: 'WAREHOUSE-B',
    reason_code: 'TRANSFER',
    reason_description: 'Stock transfer between warehouses',
    created_by: 'Alice Wilson',
  },
]

const getMovementTypeBadge = (type: string) => {
  switch (type) {
    case 'RECEIPT':
      return <Badge variant="success">Receipt</Badge>
    case 'ISSUE':
      return <Badge variant="info">Issue</Badge>
    case 'ADJUSTMENT':
      return <Badge variant="warning">Adjustment</Badge>
    case 'TRANSFER':
      return <Badge variant="default">Transfer</Badge>
    case 'RETURN':
      return <Badge variant="default">Return</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getMovementIcon = (type: string, quantity: number) => {
  if (type === 'TRANSFER') {
    return <ArrowsRightLeftIcon className="h-4 w-4 text-blue-500" />
  }
  return quantity > 0 ? (
    <ArrowUpIcon className="h-4 w-4 text-green-500" />
  ) : (
    <ArrowDownIcon className="h-4 w-4 text-red-500" />
  )
}

export default function StockMovementsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedMovement, setSelectedMovement] = useState<StockMovement | null>(null)

  const { data: stockMovements, isLoading } = useQuery({
    queryKey: ['stock-movements'],
    queryFn: () => Promise.resolve(mockStockMovements),
  })

  const columns: ColumnDef<StockMovement>[] = [
    {
      accessorKey: 'movement_number',
      header: 'Movement #',
    },
    {
      accessorKey: 'movement_date',
      header: 'Date',
      cell: ({ row }) => {
        const date = row.getValue('movement_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'movement_type',
      header: 'Type',
      cell: ({ row }) => {
        return getMovementTypeBadge(row.getValue('movement_type'))
      },
    },
    {
      id: 'direction',
      header: '',
      cell: ({ row }) => {
        const movement = row.original
        return getMovementIcon(movement.movement_type, movement.quantity_moved)
      },
    },
    {
      accessorKey: 'stock_code',
      header: 'Stock Code',
    },
    {
      accessorKey: 'description',
      header: 'Description',
    },
    {
      accessorKey: 'quantity_moved',
      header: 'Quantity',
      cell: ({ row }) => {
        const quantity = row.getValue('quantity_moved') as number
        return (
          <span className={quantity > 0 ? 'text-green-600' : 'text-red-600'}>
            {quantity > 0 ? '+' : ''}{quantity.toLocaleString()}
          </span>
        )
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
      accessorKey: 'total_value',
      header: 'Total Value',
      cell: ({ row }) => {
        const value = parseFloat(row.getValue('total_value'))
        return (
          <span className={value > 0 ? 'text-green-600' : 'text-red-600'}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(value)}
          </span>
        )
      },
    },
    {
      accessorKey: 'quantity_before',
      header: 'Qty Before',
      cell: ({ row }) => {
        const quantity = row.getValue('quantity_before') as number
        return quantity.toLocaleString()
      },
    },
    {
      accessorKey: 'quantity_after',
      header: 'Qty After',
      cell: ({ row }) => {
        const quantity = row.getValue('quantity_after') as number
        return quantity.toLocaleString()
      },
    },
    {
      accessorKey: 'reference',
      header: 'Reference',
    },
    {
      accessorKey: 'location_from',
      header: 'From Location',
    },
    {
      accessorKey: 'location_to',
      header: 'To Location',
    },
    {
      accessorKey: 'reason_code',
      header: 'Reason',
    },
    {
      accessorKey: 'created_by',
      header: 'Created By',
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const movement = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedMovement(movement)
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch(`/api/v1/stock/movements/${movement.id}/print`, {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  if (response.ok) {
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `stock-movement-${movement.movement_number}.pdf`
                    link.click()
                    window.URL.revokeObjectURL(url)
                  } else {
                    console.error('Failed to print movement')
                  }
                } catch (error) {
                  console.error('Error printing movement:', error)
                }
              }}
            >
              <DocumentTextIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'movement_type',
      label: 'Movement Type',
      type: 'select',
      required: true,
      options: [
        { value: 'RECEIPT', label: 'Receipt' },
        { value: 'ISSUE', label: 'Issue' },
        { value: 'ADJUSTMENT', label: 'Adjustment' },
        { value: 'TRANSFER', label: 'Transfer' },
        { value: 'RETURN', label: 'Return' },
      ],
    },
    {
      name: 'stock_code',
      label: 'Stock Item',
      type: 'select',
      required: true,
      options: [
        { value: 'ITEM001', label: 'ITEM001 - Computer Mouse - Optical' },
        { value: 'ITEM002', label: 'ITEM002 - Keyboard - Mechanical' },
        { value: 'ITEM003', label: 'ITEM003 - Monitor - 24" LCD' },
      ],
    },
    {
      name: 'quantity_moved',
      label: 'Quantity',
      type: 'number',
      required: true,
    },
    {
      name: 'unit_cost',
      label: 'Unit Cost',
      type: 'number',
    },
    {
      name: 'reference',
      label: 'Reference',
      type: 'text',
    },
    {
      name: 'location_from',
      label: 'From Location',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'WAREHOUSE-A', label: 'Warehouse A' },
        { value: 'WAREHOUSE-B', label: 'Warehouse B' },
        { value: 'SHOP-FLOOR', label: 'Shop Floor' },
        { value: 'RETURNS', label: 'Returns Area' },
      ],
    },
    {
      name: 'location_to',
      label: 'To Location',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'WAREHOUSE-A', label: 'Warehouse A' },
        { value: 'WAREHOUSE-B', label: 'Warehouse B' },
        { value: 'SHOP-FLOOR', label: 'Shop Floor' },
        { value: 'RETURNS', label: 'Returns Area' },
      ],
    },
    {
      name: 'reason_code',
      label: 'Reason Code',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'PURCHASE', label: 'Purchase' },
        { value: 'SALE', label: 'Sale' },
        { value: 'ADJUSTMENT', label: 'Adjustment' },
        { value: 'TRANSFER', label: 'Transfer' },
        { value: 'DAMAGE', label: 'Damage' },
        { value: 'OBSOLETE', label: 'Obsolete' },
        { value: 'RETURN', label: 'Return' },
      ],
    },
    {
      name: 'reason_description',
      label: 'Reason Description',
      type: 'text',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateMovement = (data: any) => {
    console.log('Creating stock movement:', data)
    setShowCreateModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Stock Movements"
        description="Track all stock movements and transactions"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Movements' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/stock/movements/report', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Stock Movement Report</title></head>
                        <body>
                          <h1>Stock Movement Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Stock Code</th><th>Description</th><th>Receipts</th><th>Issues</th><th>Adjustments</th><th>Net Movement</th></tr>
                            ${data.report_data?.map((row: any) => 
                              `<tr><td>${row.stock_code}</td><td>${row.description}</td><td>${row.receipts}</td><td>${row.issues}</td><td>${row.adjustments}</td><td>${row.net_movement}</td></tr>`
                            ).join('')}
                            <tr style="font-weight:bold"><td colspan="2">TOTALS</td><td>${data.totals?.receipts}</td><td>${data.totals?.issues}</td><td>${data.totals?.adjustments}</td><td>${data.totals?.net_movement}</td></tr>
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                  alert('Stock movement report generated')
                } catch (error) {
                  alert('Failed to generate movement report')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Movement Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/stock/movements/reconciliation', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({})
                  })
                  const result = await response.json()
                  alert(`Stock reconciliation completed. ${result.reconciled_items} items reconciled with ${result.discrepancies} discrepancies found.`)
                  window.location.reload()
                } catch (error) {
                  alert('Failed to perform stock reconciliation')
                }
              }}
            >
              Stock Reconciliation
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Movement
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={stockMovements || []}
        searchPlaceholder="Search stock movements..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Stock Movement"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateMovement}
          onCancel={() => setShowCreateModal(false)}
          schema={stockMovementSchema}
          submitLabel="Create Movement"
        />
      </Modal>

      {/* Movement Details Modal */}
      {selectedMovement && (
        <Modal
          isOpen={!!selectedMovement}
          onClose={() => setSelectedMovement(null)}
          title={`Stock Movement - ${selectedMovement.movement_number}`}
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-gray-900">Movement Details</h3>
                <dl className="mt-2 space-y-1">
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Type:</dt>
                    <dd className="text-sm text-gray-900">{getMovementTypeBadge(selectedMovement.movement_type)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Date:</dt>
                    <dd className="text-sm text-gray-900">{new Date(selectedMovement.movement_date).toLocaleDateString()}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Reference:</dt>
                    <dd className="text-sm text-gray-900">{selectedMovement.reference || 'N/A'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Created By:</dt>
                    <dd className="text-sm text-gray-900">{selectedMovement.created_by}</dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900">Stock Details</h3>
                <dl className="mt-2 space-y-1">
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Stock Code:</dt>
                    <dd className="text-sm text-gray-900">{selectedMovement.stock_code}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Description:</dt>
                    <dd className="text-sm text-gray-900">{selectedMovement.description}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Quantity:</dt>
                    <dd className={`text-sm ${selectedMovement.quantity_moved > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {selectedMovement.quantity_moved > 0 ? '+' : ''}{selectedMovement.quantity_moved}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Unit Cost:</dt>
                    <dd className="text-sm text-gray-900">
                      {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(selectedMovement.unit_cost)}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
            
            {selectedMovement.location_from && (
              <div>
                <h3 className="font-medium text-gray-900">Location Details</h3>
                <div className="mt-2 flex items-center space-x-2">
                  <span className="text-sm text-gray-500">From:</span>
                  <Badge variant="default">{selectedMovement.location_from}</Badge>
                  {selectedMovement.location_to && (
                    <>
                      <ArrowsRightLeftIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-500">To:</span>
                      <Badge variant="default">{selectedMovement.location_to}</Badge>
                    </>
                  )}
                </div>
              </div>
            )}
            
            {selectedMovement.reason_description && (
              <div>
                <h3 className="font-medium text-gray-900">Reason</h3>
                <p className="mt-1 text-sm text-gray-600">{selectedMovement.reason_description}</p>
              </div>
            )}
            
            {selectedMovement.notes && (
              <div>
                <h3 className="font-medium text-gray-900">Notes</h3>
                <p className="mt-1 text-sm text-gray-600">{selectedMovement.notes}</p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}