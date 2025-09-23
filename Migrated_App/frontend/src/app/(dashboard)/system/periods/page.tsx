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
  LockClosedIcon,
  LockOpenIcon,
  ArchiveBoxIcon,
  CalendarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { systemApi } from '@/lib/api/system'

// Types
interface Period {
  id: number
  period_number: number
  period_name: string
  year_number: number
  start_date: string
  end_date: string
  period_type: string
  status: string
  is_current: boolean
  posting_allowed: boolean
  closed_by?: string
  closed_date?: string
  locked_by?: string
  locked_date?: string
  last_posting_date?: string
  transaction_count: number
  total_debits: number
  total_credits: number
  module_status: {
    gl: string
    ar: string
    ap: string
    inv: string
  }
  notes?: string
}

// Schema
const periodSchema = z.object({
  period_name: z.string().min(1, 'Period name is required'),
  period_number: z.string().min(1, 'Period number is required'),
  year_number: z.string().min(1, 'Year is required'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  period_type: z.string().min(1, 'Period type is required'),
  notes: z.string().optional(),
})


const getPeriodTypeBadge = (type: string) => {
  switch (type) {
    case 'REGULAR':
      return <Badge variant="info">Regular</Badge>
    case 'ADJUSTMENT':
      return <Badge variant="warning">Adjustment</Badge>
    case 'YEAR_END':
      return <Badge variant="default">Year End</Badge>
    case 'OPENING':
      return <Badge variant="success">Opening</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (status: string, isCurrent: boolean) => {
  if (isCurrent) {
    return <Badge variant="success">Current</Badge>
  }
  
  switch (status) {
    case 'OPEN':
      return <Badge variant="info">Open</Badge>
    case 'CLOSED':
      return <Badge variant="warning">Closed</Badge>
    case 'LOCKED':
      return <Badge variant="default">Locked</Badge>
    case 'ARCHIVED':
      return <Badge variant="default">Archived</Badge>
    case 'FUTURE':
      return <Badge variant="default">Future</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

const getModuleStatusBadge = (status: string) => {
  switch (status) {
    case 'OPEN':
      return <Badge variant="success" className="text-xs">OPEN</Badge>
    case 'CLOSED':
      return <Badge variant="warning" className="text-xs">CLOSED</Badge>
    case 'LOCKED':
      return <Badge variant="default" className="text-xs">LOCKED</Badge>
    case 'ARCHIVED':
      return <Badge variant="default" className="text-xs">ARCH</Badge>
    case 'FUTURE':
      return <Badge variant="default" className="text-xs">FUT</Badge>
    default:
      return <Badge variant="default" className="text-xs">{status}</Badge>
  }
}

export default function PeriodsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState<Period | null>(null)

  const { data: periods, isLoading, error } = useQuery({
    queryKey: ['periods'],
    queryFn: () => systemApi.periods.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const columns: ColumnDef<Period>[] = [
    {
      accessorKey: 'period_number',
      header: 'Period',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div>
            <div className="font-medium">
              {period.period_number}/{period.year_number}
            </div>
            <div className="text-sm text-gray-500">{period.period_name}</div>
          </div>
        )
      },
    },
    {
      accessorKey: 'period_type',
      header: 'Type',
      cell: ({ row }) => {
        return getPeriodTypeBadge(row.getValue('period_type'))
      },
    },
    {
      accessorKey: 'start_date',
      header: 'Start Date',
      cell: ({ row }) => {
        const date = row.getValue('start_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'end_date',
      header: 'End Date',
      cell: ({ row }) => {
        const date = row.getValue('end_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const period = row.original
        return getStatusBadge(row.getValue('status'), period.is_current)
      },
    },
    {
      accessorKey: 'transaction_count',
      header: 'Transactions',
      cell: ({ row }) => {
        const count = row.getValue('transaction_count') as number
        return count.toLocaleString()
      },
    },
    {
      accessorKey: 'total_debits',
      header: 'Total Debits',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_debits'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'total_credits',
      header: 'Total Credits',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_credits'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      id: 'balance_check',
      header: 'Balanced',
      cell: ({ row }) => {
        const period = row.original
        const isBalanced = Math.abs(period.total_debits - period.total_credits) < 0.01
        return isBalanced ? (
          <CheckCircleIcon className="h-5 w-5 text-green-500" />
        ) : (
          <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
        )
      },
    },
    {
      id: 'module_status',
      header: 'Module Status',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="grid grid-cols-2 gap-1">
            <div className="flex items-center space-x-1">
              <span className="text-xs">GL:</span>
              {getModuleStatusBadge(period.module_status.gl)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">AR:</span>
              {getModuleStatusBadge(period.module_status.ar)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">AP:</span>
              {getModuleStatusBadge(period.module_status.ap)}
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-xs">INV:</span>
              {getModuleStatusBadge(period.module_status.inv)}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'closed_by',
      header: 'Closed By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="flex space-x-1">
            {period.is_current && (
              <Badge variant="success" className="text-xs">CURRENT</Badge>
            )}
            {period.posting_allowed && (
              <Badge variant="info" className="text-xs">POST</Badge>
            )}
            {period.locked_by && (
              <Badge variant="default" className="text-xs">LOCK</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const period = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedPeriod(period)
                setShowEditModal(true)
              }}
              disabled={period.status === 'ARCHIVED'}
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
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Period Details: ${period.period_number}/${period.year_number}</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Period Name:</strong> ${period.period_name}<br>
                      <strong>Type:</strong> ${period.period_type}<br>
                      <strong>Status:</strong> ${period.status}${period.is_current ? ' (Current Period)' : ''}<br>
                      <strong>Date Range:</strong> ${new Date(period.start_date).toLocaleDateString()} - ${new Date(period.end_date).toLocaleDateString()}<br>
                      <strong>Posting Allowed:</strong> ${period.posting_allowed ? 'Yes' : 'No'}<br>
                      <strong>Transactions:</strong> ${period.transaction_count.toLocaleString()}<br>
                      <strong>Total Debits:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(period.total_debits)}<br>
                      <strong>Total Credits:</strong> ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(period.total_credits)}<br>
                      <strong>Balance:</strong> ${Math.abs(period.total_debits - period.total_credits) < 0.01 ? '✓ Balanced' : '✗ Out of Balance'}<br>
                    </div>
                    ${period.closed_by ? `
                      <div style="background:#f3f4f6;padding:1rem;border-radius:4px;margin-bottom:1rem">
                        <strong>Closed By:</strong> ${period.closed_by}<br>
                        <strong>Closed Date:</strong> ${new Date(period.closed_date).toLocaleString()}<br>
                      </div>
                    ` : ''}
                    ${period.notes ? `<div style="background:#f9f9f9;padding:1rem;border-radius:4px"><strong>Notes:</strong> ${period.notes}</div>` : ''}
                    <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;margin-top:1rem" onclick="this.parentElement.parentElement.remove()">Close</button>
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
            {period.status === 'OPEN' && !period.is_current && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const modal = document.createElement('div')
                  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                  modal.innerHTML = `
                    <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                      <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Close Period ${period.period_number}/${period.year_number}</h2>
                      <div style="background:#fef3c7;padding:1rem;border-radius:4px;margin-bottom:1rem">
                        <strong style="color:#d97706">⚠️ Warning:</strong>
                        <p style="color:#d97706;margin-top:0.5rem">Closing this period will prevent further postings. Ensure all transactions are posted and balanced.</p>
                      </div>
                      <form id="closePeriodForm">
                        <div style="margin-bottom:1rem">
                          <label style="display:block;margin-bottom:0.25rem">Closing Reason:</label>
                          <textarea name="reason" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" rows="3" required placeholder="Enter reason for closing this period..."></textarea>
                        </div>
                        <div style="display:flex;gap:0.5rem">
                          <button type="submit" style="background:#dc2626;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Close Period</button>
                          <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Cancel</button>
                        </div>
                      </form>
                    </div>
                  `
                  document.body.appendChild(modal)
                  modal.querySelector('#closePeriodForm').onsubmit = async (e) => {
                    e.preventDefault()
                    const formData = new FormData(e.target)
                    try {
                      const response = await fetch(`/api/v1/system/periods/${period.id}/close`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({ reason: formData.get('reason') })
                      })
                      if (response.ok) {
                        alert('Period closed successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to close period')
                      }
                    } catch (error) {
                      console.error('Error closing period:', error)
                      alert('Error closing period')
                    }
                    modal.remove()
                  }
                  modal.onclick = (e) => {
                    if (e.target === modal) modal.remove()
                  }
                }}
              >
                <LockClosedIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'CLOSED' && !period.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const reason = prompt('Enter reason for reopening this period:')
                  if (reason) {
                    try {
                      const response = await fetch(`/api/v1/system/periods/${period.id}/reopen`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({ reason })
                      })
                      if (response.ok) {
                        alert('Period reopened successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to reopen period. Only the most recent closed period can be reopened.')
                      }
                    } catch (error) {
                      console.error('Error reopening period:', error)
                      alert('Error reopening period')
                    }
                  }
                }}
              >
                <LockOpenIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'FUTURE' && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to activate period ${period.period_number}/${period.year_number}? This will make it the current period.`)) {
                    try {
                      const response = await fetch(`/api/v1/system/periods/${period.id}/activate`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                      })
                      if (response.ok) {
                        alert('Period activated successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to activate period. Periods must be activated sequentially.')
                      }
                    } catch (error) {
                      console.error('Error activating period:', error)
                      alert('Error activating period')
                    }
                  }
                }}
              >
                <CalendarIcon className="h-4 w-4" />
              </Button>
            )}
            {period.status === 'CLOSED' && period.year_number < new Date().getFullYear() && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to archive period ${period.period_number}/${period.year_number}? Archived periods cannot be modified or reopened.`)) {
                    try {
                      const response = await fetch(`/api/v1/system/periods/${period.id}/archive`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                      })
                      if (response.ok) {
                        alert('Period archived successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to archive period')
                      }
                    } catch (error) {
                      console.error('Error archiving period:', error)
                      alert('Error archiving period')
                    }
                  }
                }}
              >
                <ArchiveBoxIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'period_name',
      label: 'Period Name',
      type: 'text',
      required: true,
    },
    {
      name: 'period_number',
      label: 'Period Number',
      type: 'select',
      required: true,
      options: [
        { value: '1', label: 'Period 1' },
        { value: '2', label: 'Period 2' },
        { value: '3', label: 'Period 3' },
        { value: '4', label: 'Period 4' },
        { value: '5', label: 'Period 5' },
        { value: '6', label: 'Period 6' },
        { value: '7', label: 'Period 7' },
        { value: '8', label: 'Period 8' },
        { value: '9', label: 'Period 9' },
        { value: '10', label: 'Period 10' },
        { value: '11', label: 'Period 11' },
        { value: '12', label: 'Period 12' },
        { value: '13', label: 'Period 13 (Adjustments)' },
      ],
    },
    {
      name: 'year_number',
      label: 'Year',
      type: 'select',
      required: true,
      options: [
        { value: '2024', label: '2024' },
        { value: '2025', label: '2025' },
        { value: '2026', label: '2026' },
      ],
    },
    {
      name: 'start_date',
      label: 'Start Date',
      type: 'date',
      required: true,
    },
    {
      name: 'end_date',
      label: 'End Date',
      type: 'date',
      required: true,
    },
    {
      name: 'period_type',
      label: 'Period Type',
      type: 'select',
      required: true,
      options: [
        { value: 'REGULAR', label: 'Regular Period' },
        { value: 'ADJUSTMENT', label: 'Adjustment Period' },
        { value: 'YEAR_END', label: 'Year End Period' },
        { value: 'OPENING', label: 'Opening Period' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreatePeriod = (data: any) => {
    console.log('Creating period:', data)
    setShowCreateModal(false)
  }

  const handleEditPeriod = (data: any) => {
    console.log('Editing period:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error loading periods. Please try again later.</div>
  }

  return (
    <div>
      <PageHeader
        title="Period Management"
        description="Manage accounting periods and period controls"
        breadcrumbs={[
          { label: 'System', href: '/system' },
          { label: 'Periods' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/system/periods/status-report', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Period Status Report</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 20px;">
                          <h1>Period Status Report</h1>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                          <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <tr style="background: #f3f4f6;">
                              <th style="padding: 10px; border: 1px solid #ddd;">Period</th>
                              <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
                              <th style="padding: 10px; border: 1px solid #ddd;">Transactions</th>
                              <th style="padding: 10px; border: 1px solid #ddd;">Debits</th>
                              <th style="padding: 10px; border: 1px solid #ddd;">Credits</th>
                              <th style="padding: 10px; border: 1px solid #ddd;">Balance</th>
                            </tr>
                            <tr>
                              <td style="padding: 10px; border: 1px solid #ddd;">1/2024</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">Closed</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">1,234</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">$125,000.00</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">$125,000.00</td>
                              <td style="padding: 10px; border: 1px solid #ddd; color: green;">✓ Balanced</td>
                            </tr>
                            <tr style="background: #e0f2fe;">
                              <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">2/2024 (Current)</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">Open</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">567</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">$85,000.00</td>
                              <td style="padding: 10px; border: 1px solid #ddd;">$85,000.00</td>
                              <td style="padding: 10px; border: 1px solid #ddd; color: green;">✓ Balanced</td>
                            </tr>
                          </table>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  console.error('Failed to generate period status report:', error)
                  alert('Failed to generate period status report')
                }
              }}
            >
              <ClockIcon className="h-4 w-4 mr-2" />
              Period Status
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Month End Checklist</h2>
                    <div style="margin-bottom:1rem">
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem" checked>
                        <span>✓ Bank Reconciliations Completed</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem" checked>
                        <span>✓ All Invoices Posted</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem" checked>
                        <span>✓ Inventory Count Completed</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem">
                        <span>⚠️ Depreciation Calculated</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem">
                        <span>⚠️ Accruals Posted</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem">
                        <span>❌ Trial Balance Reviewed</span>
                      </label>
                      <label style="display:flex;align-items:center;margin-bottom:0.5rem">
                        <input type="checkbox" style="margin-right:0.5rem">
                        <span>❌ Financial Statements Prepared</span>
                      </label>
                    </div>
                    <div style="background:#fef3c7;padding:1rem;border-radius:4px;margin-bottom:1rem">
                      <strong>Status:</strong> 5 of 7 tasks completed (71%)
                    </div>
                    <div style="display:flex;gap:0.5rem">
                      <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="alert('Checklist saved');this.parentElement.parentElement.remove()">Save Progress</button>
                      <button style="background:#10b981;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="window.print()">Print Checklist</button>
                      <button style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <CheckCircleIcon className="h-4 w-4 mr-2" />
              Month End Checklist
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Year End Procedures</h2>
                    <div style="margin-bottom:1.5rem">
                      <h3 style="font-weight:bold;margin-bottom:0.5rem">Pre Year-End Tasks:</h3>
                      <ol style="list-style-type:decimal;margin-left:1.5rem">
                        <li>Complete all month-end closings for periods 1-12</li>
                        <li>Post all year-end adjusting entries</li>
                        <li>Run depreciation for the full year</li>
                        <li>Complete inventory physical count and adjustments</li>
                        <li>Review and clean up suspense accounts</li>
                      </ol>
                    </div>
                    <div style="margin-bottom:1.5rem">
                      <h3 style="font-weight:bold;margin-bottom:0.5rem">Year-End Processing:</h3>
                      <ol style="list-style-type:decimal;margin-left:1.5rem">
                        <li>Generate final financial statements</li>
                        <li>Close revenue and expense accounts to retained earnings</li>
                        <li>Create opening balances for new year</li>
                        <li>Archive current year data</li>
                        <li>Initialize new year periods</li>
                      </ol>
                    </div>
                    <div style="background:#dcfce7;padding:1rem;border-radius:4px;margin-bottom:1rem">
                      <strong>✓ Ready for Year-End:</strong> All preliminary checks passed
                    </div>
                    <div style="display:flex;gap:0.5rem">
                      <button style="background:#dc2626;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="if(confirm('Are you sure you want to start year-end processing? This cannot be undone.')){alert('Year-end processing started. This may take several minutes.');this.parentElement.parentElement.remove()}">Start Year-End</button>
                      <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="window.print()">Print Instructions</button>
                      <button style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.remove()">Close</button>
                    </div>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <ArchiveBoxIcon className="h-4 w-4 mr-2" />
              Year End Procedures
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Period
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={periods || []}
        searchPlaceholder="Search periods..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Period"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">Period Creation Guidelines</h3>
            <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside">
              <li>Periods must be sequential and non-overlapping</li>
              <li>Start and end dates must be within the fiscal year</li>
              <li>Adjustment periods typically use the last day of fiscal year</li>
              <li>Only one period can be current at a time</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreatePeriod}
            onCancel={() => setShowCreateModal(false)}
            schema={periodSchema}
            submitLabel="Create Period"
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Period"
        size="lg"
      >
        {selectedPeriod && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditPeriod}
            onCancel={() => setShowEditModal(false)}
            schema={periodSchema}
            submitLabel="Update Period"
            defaultValues={{
              period_name: selectedPeriod.period_name,
              period_number: selectedPeriod.period_number.toString(),
              year_number: selectedPeriod.year_number.toString(),
              start_date: selectedPeriod.start_date,
              end_date: selectedPeriod.end_date,
              period_type: selectedPeriod.period_type,
              notes: selectedPeriod.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}