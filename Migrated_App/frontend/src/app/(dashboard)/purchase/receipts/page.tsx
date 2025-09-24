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
  TruckIcon,
  DocumentCheckIcon,
  ClipboardDocumentIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { goodsReceiptsApi, GoodsReceipt } from '@/lib/api/goods-receipts'
import toast from 'react-hot-toast'

// Schema
const goodsReceiptSchema = z.object({
  supplier_code: z.string().min(1, 'Supplier is required'),
  order_number: z.string().optional(),
  delivery_note: z.string().optional(),
  notes: z.string().optional(),
  receipt_lines: z.array(z.object({
    stock_code: z.string().min(1, 'Stock code is required'),
    description: z.string().min(1, 'Description is required'),
    quantity_received: z.string().min(1, 'Quantity is required'),
    unit_cost: z.string().min(1, 'Unit cost is required'),
  })).min(1, 'At least one receipt line is required'),
})


const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'PARTIAL':
      return <Badge variant="info">Partial</Badge>
    case 'RECEIVED':
      return <Badge variant="success">Received</Badge>
    case 'CANCELLED':
      return <Badge variant="danger">Cancelled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function GoodsReceiptsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedReceipt, setSelectedReceipt] = useState<GoodsReceipt | null>(null)

  const { data: goodsReceipts, isLoading, error, refetch } = useQuery({
    queryKey: ['goods-receipts'],
    queryFn: () => goodsReceiptsApi.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const columns: ColumnDef<GoodsReceipt>[] = [
    {
      accessorKey: 'receipt_number',
      header: 'Receipt Number',
    },
    {
      accessorKey: 'receipt_date',
      header: 'Receipt Date',
      cell: ({ row }) => {
        const date = row.getValue('receipt_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'supplier_code',
      header: 'Supplier',
    },
    {
      accessorKey: 'supplier_name',
      header: 'Supplier Name',
    },
    {
      accessorKey: 'order_number',
      header: 'PO Number',
    },
    {
      accessorKey: 'delivery_note',
      header: 'Delivery Note',
    },
    {
      accessorKey: 'total_quantity',
      header: 'Total Qty',
      cell: ({ row }) => {
        const quantity = row.getValue('total_quantity') as number
        return quantity ? quantity.toLocaleString() : '0'
      },
    },
    {
      accessorKey: 'goods_received',
      header: 'Received',
      cell: ({ row }) => {
        const received = row.getValue('goods_received') as number
        const total = row.original.total_quantity
        return (
          <span className={received < total ? 'text-orange-600' : 'text-green-600'}>
            {received ? received.toLocaleString() : '0'}
          </span>
        )
      },
    },
    {
      accessorKey: 'outstanding_quantity',
      header: 'Outstanding',
      cell: ({ row }) => {
        const outstanding = row.getValue('outstanding_quantity') as number
        return (
          <span className={outstanding > 0 ? 'text-red-600 font-semibold' : ''}>
            {outstanding ? outstanding.toLocaleString() : '0'}
          </span>
        )
      },
    },
    {
      accessorKey: 'total_value',
      header: 'Total Value',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_value'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'receipt_status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('receipt_status'))
      },
    },
    {
      accessorKey: 'received_by',
      header: 'Received By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const receipt = row.original
        return (
          <div className="flex space-x-1">
            {receipt.gl_posted && (
              <Badge variant="success" className="text-xs">GL</Badge>
            )}
            {receipt.is_complete && (
              <Badge variant="info" className="text-xs">Complete</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const receipt = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedReceipt(receipt)
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
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Goods Receipt Details</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Receipt Number:</strong> ${receipt.receipt_number}<br>
                      <strong>Date:</strong> ${new Date(receipt.receipt_date).toLocaleDateString()}<br>
                      <strong>Order Number:</strong> ${receipt.order_number}<br>
                      <strong>Supplier:</strong> ${receipt.supplier_code} - ${receipt.supplier_name}<br>
                      <strong>Delivery Note:</strong> ${receipt.delivery_note || 'N/A'}<br>
                      <strong>Total Items:</strong> ${receipt.receipt_lines?.length || 0}<br>
                      <strong>Total Amount:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(receipt.total_value)}<br>
                      <strong>Status:</strong> ${receipt.receipt_status}${receipt.gl_posted ? ' (Posted to GL)' : ''}
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
                  const response = await fetch(`/api/v1/purchase/receipts/${receipt.id}/print`, {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  if (response.ok) {
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `goods-receipt-${receipt.receipt_number}.pdf`
                    link.click()
                    window.URL.revokeObjectURL(url)
                  } else {
                    console.error('Failed to print receipt')
                  }
                } catch (error) {
                  console.error('Error printing receipt:', error)
                }
              }}
            >
              <ClipboardDocumentIcon className="h-4 w-4" />
            </Button>
            {!receipt.gl_posted && receipt.is_complete && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to post receipt ${receipt.receipt_number} to General Ledger?`)) {
                    try {
                      const response = await fetch(`/api/v1/purchase/receipts/${receipt.id}/post-gl`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                      })
                      if (response.ok) {
                        alert('Receipt posted to GL successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to post receipt to GL')
                      }
                    } catch (error) {
                      console.error('Error posting to GL:', error)
                      alert('Error posting receipt to GL')
                    }
                  }
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
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
      label: 'Supplier',
      type: 'select',
      required: true,
      options: [
        { value: 'SUPP001', label: 'SUPP001 - ABC Supplies Ltd' },
        { value: 'SUPP002', label: 'SUPP002 - Tech Components Inc' },
        { value: 'SUPP003', label: 'SUPP003 - Office Supplies Co' },
      ],
    },
    {
      name: 'order_number',
      label: 'Purchase Order Number',
      type: 'text',
    },
    {
      name: 'delivery_note',
      label: 'Delivery Note Number',
      type: 'text',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateReceipt = (data: any) => {
    console.log('Creating goods receipt:', data)
    setShowCreateModal(false)
  }

  const handleEditReceipt = (data: any) => {
    console.log('Editing goods receipt:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading goods receipts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load goods receipts</p>
          <Button onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Goods Receipts"
        description="Manage incoming goods and deliveries"
        breadcrumbs={[
          { label: 'Purchase Ledger', href: '/purchase' },
          { label: 'Goods Receipts' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/purchase/receipts/goods-received-report', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Goods Received Report</title></head>
                        <body>
                          <h1>Goods Received Report</h1>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Date</th><th>Receipt #</th><th>Supplier</th><th>PO #</th><th>Total</th><th>Status</th></tr>
                            ${data.receipts?.map((r: any) => 
                              `<tr><td>${new Date(r.receipt_date).toLocaleDateString()}</td><td>${r.receipt_number}</td><td>${r.supplier_code}</td><td>${r.order_number}</td><td>$${r.total_value.toFixed(2)}</td><td>${r.status}</td></tr>`
                            ).join('')}
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  console.error('Failed to generate goods received report:', error)
                  alert('Failed to generate goods received report')
                }
              }}
            >
              <TruckIcon className="h-4 w-4 mr-2" />
              Received Report
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Receipt
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={goodsReceipts || []}
        searchPlaceholder="Search goods receipts..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Goods Receipt"
        size="lg"
      >
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateReceipt}
          onCancel={() => setShowCreateModal(false)}
          schema={goodsReceiptSchema}
          submitLabel="Create Receipt"
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Goods Receipt"
        size="lg"
      >
        {selectedReceipt && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditReceipt}
            onCancel={() => setShowEditModal(false)}
            schema={goodsReceiptSchema}
            submitLabel="Update Receipt"
            defaultValues={{
              supplier_code: selectedReceipt.supplier_code,
              order_number: selectedReceipt.order_number,
              delivery_note: selectedReceipt.delivery_note,
              notes: selectedReceipt.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}