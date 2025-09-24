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
import { apiRequest } from '@/lib/utils/api'
import { 
  PlusIcon, 
  EyeIcon, 
  PencilIcon, 
  ClipboardDocumentCheckIcon,
  DocumentCheckIcon,
  PrinterIcon,
  CalculatorIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface StockTake {
  id: number
  take_number: string
  take_date: string
  take_status: string
  location: string
  take_type: string
  counted_by?: string
  checked_by?: string
  authorized_by?: string
  total_items: number
  items_counted: number
  items_pending: number
  variance_count: number
  variance_value: number
  adjustment_posted: boolean
  notes?: string
  created_at: string
  completed_at?: string
}

// Schema
const stockTakeSchema = z.object({
  location: z.string().min(1, 'Location is required'),
  take_type: z.string().min(1, 'Take type is required'),
  notes: z.string().optional(),
})

// Mock data
const mockStockTakes: StockTake[] = [
  {
    id: 1,
    take_number: 'ST001234',
    take_date: '2024-01-15',
    take_status: 'COMPLETED',
    location: 'WAREHOUSE-A',
    take_type: 'FULL',
    counted_by: 'John Smith',
    checked_by: 'Jane Doe',
    authorized_by: 'Manager',
    total_items: 150,
    items_counted: 150,
    items_pending: 0,
    variance_count: 5,
    variance_value: -125.50,
    adjustment_posted: true,
    notes: 'Annual stock take - all areas covered',
    created_at: '2024-01-15T09:00:00Z',
    completed_at: '2024-01-15T17:30:00Z',
  },
  {
    id: 2,
    take_number: 'ST001235',
    take_date: '2024-01-20',
    take_status: 'IN_PROGRESS',
    location: 'WAREHOUSE-B',
    take_type: 'PARTIAL',
    counted_by: 'Bob Johnson',
    total_items: 75,
    items_counted: 45,
    items_pending: 30,
    variance_count: 2,
    variance_value: 50.00,
    adjustment_posted: false,
    notes: 'Fast-moving items check',
    created_at: '2024-01-20T08:00:00Z',
  },
  {
    id: 3,
    take_number: 'ST001236',
    take_date: '2024-01-22',
    take_status: 'PLANNED',
    location: 'SHOP-FLOOR',
    take_type: 'CYCLE',
    total_items: 25,
    items_counted: 0,
    items_pending: 25,
    variance_count: 0,
    variance_value: 0.00,
    adjustment_posted: false,
    notes: 'Monthly cycle count - high value items',
    created_at: '2024-01-22T00:00:00Z',
  },
]

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PLANNED':
      return <Badge variant="default">Planned</Badge>
    case 'IN_PROGRESS':
      return <Badge variant="warning">In Progress</Badge>
    case 'COMPLETED':
      return <Badge variant="info">Completed</Badge>
    case 'AUTHORIZED':
      return <Badge variant="success">Authorized</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getTakeTypeBadge = (type: string) => {
  switch (type) {
    case 'FULL':
      return <Badge variant="info">Full Count</Badge>
    case 'PARTIAL':
      return <Badge variant="warning">Partial Count</Badge>
    case 'CYCLE':
      return <Badge variant="default">Cycle Count</Badge>
    case 'SPOT':
      return <Badge variant="default">Spot Check</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

export default function StockTakesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedTake, setSelectedTake] = useState<StockTake | null>(null)

  const { data: stockTakes, isLoading } = useQuery({
    queryKey: ['stock-takes'],
    queryFn: async () => {
      const response = await apiRequest('/api/v1/stock/takes')
      if (!response.ok) {
        throw new Error('Failed to fetch stock takes')
      }
      const result = await response.json()
      return result.data || []
    },
  })

  const columns: ColumnDef<StockTake>[] = [
    {
      accessorKey: 'take_number',
      header: 'Take Number',
    },
    {
      accessorKey: 'take_date',
      header: 'Take Date',
      cell: ({ row }) => {
        const date = row.getValue('take_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'take_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('take_status'))
      },
    },
    {
      accessorKey: 'location',
      header: 'Location',
    },
    {
      accessorKey: 'take_type',
      header: 'Type',
      cell: ({ row }) => {
        return getTakeTypeBadge(row.getValue('take_type'))
      },
    },
    {
      accessorKey: 'total_items',
      header: 'Total Items',
      cell: ({ row }) => {
        const total = row.getValue('total_items') as number
        return (total || 0).toLocaleString()
      },
    },
    {
      accessorKey: 'items_counted',
      header: 'Counted',
      cell: ({ row }) => {
        const counted = row.getValue('items_counted') as number || 0
        const total = row.original.total_items || 0
        const percentage = total > 0 ? (counted / total * 100).toFixed(1) : '0.0'
        return (
          <span className={counted < total ? 'text-orange-600' : 'text-green-600'}>
            {counted.toLocaleString()} ({percentage}%)
          </span>
        )
      },
    },
    {
      accessorKey: 'items_pending',
      header: 'Pending',
      cell: ({ row }) => {
        const pending = row.getValue('items_pending') as number || 0
        return (
          <span className={pending > 0 ? 'text-red-600 font-semibold' : ''}>
            {pending.toLocaleString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'variance_count',
      header: 'Variances',
      cell: ({ row }) => {
        const variances = row.getValue('variance_count') as number
        return (
          <span className={variances > 0 ? 'text-orange-600 font-semibold' : 'text-green-600'}>
            {variances.toLocaleString()}
          </span>
        )
      },
    },
    {
      accessorKey: 'variance_value',
      header: 'Variance Value',
      cell: ({ row }) => {
        const value = parseFloat(row.getValue('variance_value'))
        return (
          <span className={value !== 0 ? (value > 0 ? 'text-green-600' : 'text-red-600') : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(value)}
          </span>
        )
      },
    },
    {
      accessorKey: 'counted_by',
      header: 'Counted By',
    },
    {
      accessorKey: 'checked_by',
      header: 'Checked By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const take = row.original
        return (
          <div className="flex space-x-1">
            {take.adjustment_posted && (
              <Badge variant="success" className="text-xs">ADJ</Badge>
            )}
            {take.authorized_by && (
              <Badge variant="info" className="text-xs">AUTH</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const take = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedTake(take)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Stock Take Details</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Take Number:</strong> ${take.take_number}<br>
                      <strong>Date:</strong> ${new Date(take.take_date).toLocaleDateString()}<br>
                      <strong>Location:</strong> ${take.location || 'All Locations'}<br>
                      <strong>Status:</strong> ${take.status}<br>
                      <strong>Items Counted:</strong> ${take.items_counted || 0}<br>
                      <strong>Total Variance:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(take.variance_value || 0)}<br>
                      ${take.completed_date ? `<strong>Completed:</strong> ${new Date(take.completed_date).toLocaleDateString()}<br>` : ''}
                      ${take.posted_date ? `<strong>Posted:</strong> ${new Date(take.posted_date).toLocaleDateString()}<br>` : ''}
                    </div>
                    <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/stock/takes/counting-sheets', {
                    method: 'POST',
                    body: JSON.stringify({ 
                      take_id: take.id,
                      location: take.location || 'ALL' 
                    })
                  })
                  if (response.ok) {
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `counting-sheets-${take.take_number}.pdf`
                    link.click()
                    window.URL.revokeObjectURL(url)
                  } else {
                    console.error('Failed to print counting sheets')
                  }
                } catch (error) {
                  console.error('Error printing counting sheets:', error)
                }
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {take.take_status === 'COMPLETED' && !take.adjustment_posted && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to post adjustments for stock take ${take.take_number}?`)) {
                    try {
                      const response = await apiRequest(`/api/v1/stock/takes/${take.id}/post-adjustments`, {
                        method: 'POST'
                      })
                      if (response.ok) {
                        alert('Stock take adjustments posted successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to post adjustments')
                      }
                    } catch (error) {
                      console.error('Error posting adjustments:', error)
                      alert('Error posting adjustments')
                    }
                  }
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {take.take_status === 'IN_PROGRESS' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const modal = document.createElement('div')
                  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                  modal.innerHTML = `
                    <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                      <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Stock Counting Interface</h2>
                      <form id="countForm">
                        <div style="margin-bottom:1rem">
                          <label style="display:block;margin-bottom:0.25rem">Stock Code:</label>
                          <input type="text" name="stock_code" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" placeholder="Enter stock code" required>
                        </div>
                        <div style="margin-bottom:1rem">
                          <label style="display:block;margin-bottom:0.25rem">Counted Quantity:</label>
                          <input type="number" name="quantity" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" placeholder="0" required>
                        </div>
                        <div style="display:flex;gap:0.5rem">
                          <button type="submit" style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Save Count</button>
                          <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Close</button>
                        </div>
                      </form>
                    </div>
                  `
                  document.body.appendChild(modal)
                  modal.querySelector('#countForm').onsubmit = (e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    alert(`Count saved for ${formData.get('stock_code')}: ${formData.get('quantity')}`)
                    e.target.reset()
                  }
                  modal.onclick = (e) => {
                    if (e.target === modal) modal.remove()
                  }
                }}
              >
                <CalculatorIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      required: true,
      options: [
        { value: 'WAREHOUSE-A', label: 'Warehouse A' },
        { value: 'WAREHOUSE-B', label: 'Warehouse B' },
        { value: 'SHOP-FLOOR', label: 'Shop Floor' },
        { value: 'RETURNS', label: 'Returns Area' },
        { value: 'ALL', label: 'All Locations' },
      ],
    },
    {
      name: 'take_type',
      label: 'Take Type',
      type: 'select',
      required: true,
      options: [
        { value: 'FULL', label: 'Full Stock Take' },
        { value: 'PARTIAL', label: 'Partial Count' },
        { value: 'CYCLE', label: 'Cycle Count' },
        { value: 'SPOT', label: 'Spot Check' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateTake = (data: any) => {
    console.log('Creating stock take:', data)
    setShowCreateModal(false)
  }

  const handleEditTake = (data: any) => {
    console.log('Editing stock take:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Stock Takes"
        description="Manage stock counting and inventory verification"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Takes' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/stock/takes/variance-report')
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Stock Take Variance Report</title></head>
                        <body>
                          <h1>Stock Take Variance Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Stock Code</th><th>Description</th><th>System Qty</th><th>Counted Qty</th><th>Variance</th><th>Value</th></tr>
                            ${data.variances?.map((row: any) => 
                              `<tr><td>${row.stock_code}</td><td>${row.description}</td><td>${row.system_qty}</td><td>${row.counted_qty}</td><td>${row.variance}</td><td>$${row.variance_value}</td></tr>`
                            ).join('')}
                            <tr style="font-weight:bold"><td colspan="4">TOTAL VARIANCE</td><td>${data.total_variance_qty}</td><td>$${data.total_variance_value}</td></tr>
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                  alert('Variance report generated')
                } catch (error) {
                  alert('Failed to generate variance report')
                }
              }}
            >
              Variance Report
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await apiRequest('/api/v1/stock/takes/counting-sheets', {
                    method: 'POST',
                    body: JSON.stringify({ location: 'ALL' })
                  })
                  const blob = await response.blob()
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `counting-sheets-${new Date().toISOString().split('T')[0]}.pdf`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                  window.URL.revokeObjectURL(url)
                  alert('Counting sheets downloaded')
                } catch (error) {
                  alert('Failed to download counting sheets')
                }
              }}
            >
              <ClipboardDocumentCheckIcon className="h-4 w-4 mr-2" />
              Counting Sheets
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Stock Take
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={stockTakes || []}
        searchPlaceholder="Search stock takes..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Stock Take"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateTake}
          onCancel={() => setShowCreateModal(false)}
          schema={stockTakeSchema}
          submitLabel="Create Stock Take"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Stock Take"
        size="lg"
      >
        {selectedTake && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditTake}
            onCancel={() => setShowEditModal(false)}
            schema={stockTakeSchema}
            submitLabel="Update Stock Take"
            defaultValues={{
              location: selectedTake.location,
              take_type: selectedTake.take_type,
              notes: selectedTake.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}