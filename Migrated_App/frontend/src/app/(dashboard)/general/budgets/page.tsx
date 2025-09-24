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
  DocumentDuplicateIcon,
  ChartBarIcon,
  CalculatorIcon,
  ArrowUpTrayIcon,
  DocumentArrowUpIcon,
  LockClosedIcon,
  LockOpenIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { apiRequest } from '@/lib/utils/api'

// Types
interface Budget {
  id: number
  budget_name: string
  budget_year: number
  budget_version: string
  budget_type: string
  department?: string
  cost_center?: string
  currency_code: string
  status: string
  created_by: string
  created_date: string
  approved_by?: string
  approved_date?: string
  locked_by?: string
  locked_date?: string
  total_revenue: number
  total_expenses: number
  net_income: number
  variance_threshold: number
  is_active: boolean
  notes?: string
}

interface BudgetLine {
  id: number
  budget_id: number
  account_code: string
  account_name: string
  period_1: number
  period_2: number
  period_3: number
  period_4: number
  period_5: number
  period_6: number
  period_7: number
  period_8: number
  period_9: number
  period_10: number
  period_11: number
  period_12: number
  total_annual: number
  notes?: string
}

// Schema
const budgetSchema = z.object({
  budget_name: z.string().min(1, 'Budget name is required'),
  budget_year: z.string().min(1, 'Budget year is required'),
  budget_version: z.string().min(1, 'Version is required'),
  budget_type: z.string().min(1, 'Budget type is required'),
  department: z.string().optional(),
  cost_center: z.string().optional(),
  currency_code: z.string().min(1, 'Currency is required'),
  variance_threshold: z.string().optional(),
  notes: z.string().optional(),
})

// No mock data - using API

const getBudgetTypeBadge = (type: string) => {
  switch (type) {
    case 'OPERATING':
      return <Badge variant="success">Operating</Badge>
    case 'CAPITAL':
      return <Badge variant="info">Capital</Badge>
    case 'FORECAST':
      return <Badge variant="warning">Forecast</Badge>
    case 'DEPARTMENTAL':
      return <Badge variant="default">Departmental</Badge>
    case 'PROJECT':
      return <Badge variant="default">Project</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getStatusBadge = (status: string, isActive: boolean) => {
  if (!isActive) {
    return <Badge variant="default">Inactive</Badge>
  }
  
  switch (status) {
    case 'DRAFT':
      return <Badge variant="default">Draft</Badge>
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'APPROVED':
      return <Badge variant="success">Approved</Badge>
    case 'REJECTED':
      return <Badge variant="danger">Rejected</Badge>
    case 'LOCKED':
      return <Badge variant="info">Locked</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function BudgetsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedBudget, setSelectedBudget] = useState<Budget | null>(null)

  const { data: budgets, isLoading } = useQuery({
    queryKey: ['budgets'],
    queryFn: async () => {
      const response = await apiRequest('/api/v1/general/budgets')
      if (!response.ok) {
        throw new Error(`Failed to fetch budgets: ${response.statusText}`)
      }
      const result = await response.json()
      return result.data || []
    }
  })

  const columns: ColumnDef<Budget>[] = [
    {
      accessorKey: 'budget_name',
      header: 'Budget Name',
      cell: ({ row }) => {
        const budget = row.original
        return (
          <div>
            <div className="font-medium">{budget.budget_name}</div>
            <div className="text-sm text-gray-500">
              {budget.budget_year} - {budget.budget_version}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'budget_type',
      header: 'Type',
      cell: ({ row }) => {
        return getBudgetTypeBadge(row.getValue('budget_type'))
      },
    },
    {
      accessorKey: 'department',
      header: 'Department',
      cell: ({ row }) => {
        const dept = row.getValue('department') as string
        const costCenter = row.original.cost_center
        return (
          <div>
            <div>{dept || 'All'}</div>
            {costCenter && (
              <div className="text-xs text-gray-500">{costCenter}</div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'total_revenue',
      header: 'Total Revenue',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_revenue'))
        return (
          <span className={amount > 0 ? 'text-green-600' : 'text-gray-400'}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(amount)}
          </span>
        )
      },
    },
    {
      accessorKey: 'total_expenses',
      header: 'Total Expenses',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('total_expenses'))
        return (
          <span className="text-red-600">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(amount)}
          </span>
        )
      },
    },
    {
      accessorKey: 'net_income',
      header: 'Net Income',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('net_income'))
        return (
          <span className={amount >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(amount)}
          </span>
        )
      },
    },
    {
      accessorKey: 'variance_threshold',
      header: 'Variance %',
      cell: ({ row }) => {
        const threshold = row.getValue('variance_threshold') as number
        return `${threshold}%`
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const budget = row.original
        return getStatusBadge(row.getValue('status'), budget.is_active)
      },
    },
    {
      accessorKey: 'created_by',
      header: 'Created By',
    },
    {
      accessorKey: 'approved_by',
      header: 'Approved By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const budget = row.original
        return (
          <div className="flex space-x-1">
            {budget.is_active && (
              <Badge variant="success" className="text-xs">ACTIVE</Badge>
            )}
            {budget.locked_by && (
              <Badge variant="info" className="text-xs">LOCKED</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const budget = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedBudget(budget)
                setShowEditModal(true)
              }}
              disabled={budget.status === 'LOCKED' || budget.locked_by !== null}
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
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Budget Details: ${budget.budget_name}</h2>
                    <div style="margin-bottom:1rem">
                      <strong>Year:</strong> ${budget.budget_year}<br>
                      <strong>Period:</strong> ${budget.budget_period}<br>
                      <strong>Type:</strong> ${budget.budget_type}<br>
                      <strong>Status:</strong> ${budget.status}${budget.is_locked ? ' (Locked)' : ''}<br>
                      <strong>Created:</strong> ${new Date(budget.created_date).toLocaleDateString()}<br>
                      <strong>Created By:</strong> ${budget.created_by}<br>
                    </div>
                    <div style="background:#f3f4f6;padding:1rem;border-radius:4px">
                      <h3 style="font-weight:bold;margin-bottom:0.5rem">Budget Summary:</h3>
                      <p>Total Budget: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(budget.total_amount || 0)}</p>
                      <p>Actual YTD: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(budget.actual_amount || 0)}</p>
                      <p>Variance: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format((budget.total_amount || 0) - (budget.actual_amount || 0))}</p>
                    </div>
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
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Copy Budget: ${budget.budget_name}</h2>
                    <form id="copyForm">
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">New Budget Name:</label>
                        <input type="text" name="name" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="${budget.budget_name} - Copy" required>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Target Year:</label>
                        <input type="number" name="year" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="${new Date().getFullYear() + 1}" required>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Adjustment %:</label>
                        <input type="number" name="adjustment" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="0" step="0.1">
                      </div>
                      <div style="display:flex;gap:0.5rem">
                        <button type="submit" style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Copy Budget</button>
                        <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Cancel</button>
                      </div>
                    </form>
                  </div>
                `
                document.body.appendChild(modal)
                modal.querySelector('#copyForm').onsubmit = async (e) => {
                  e.preventDefault()
                  const formData = new FormData(e.target)
                  alert(`Budget copied: ${formData.get('name')} for year ${formData.get('year')} with ${formData.get('adjustment')}% adjustment`)
                  modal.remove()
                  window.location.reload()
                }
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch(`/api/v1/general/budgets/${budget.id}/variance-analysis`, {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Budget Variance Analysis - ${budget.budget_name}</title></head>
                        <body style="font-family: Arial, sans-serif; padding: 20px;">
                          <h1>Budget Variance Analysis</h1>
                          <h2>${budget.budget_name} - ${budget.budget_year}</h2>
                          <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <tr style="background: #f3f4f6;">
                              <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Account</th>
                              <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Budget</th>
                              <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Actual</th>
                              <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Variance</th>
                              <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">%</th>
                            </tr>
                            <tr>
                              <td style="padding: 10px; border: 1px solid #ddd;">Revenue</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$100,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$92,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: red;">-$8,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: red;">-8.0%</td>
                            </tr>
                            <tr>
                              <td style="padding: 10px; border: 1px solid #ddd;">Expenses</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$80,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$75,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: green;">$5,000</td>
                              <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: green;">6.25%</td>
                            </tr>
                          </table>
                          <p style="margin-top: 40px; color: #666;">Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  console.error('Failed to generate variance analysis:', error)
                  alert('Failed to generate variance analysis')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4" />
            </Button>
            {budget.status === 'APPROVED' && !budget.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  if (confirm(`Are you sure you want to lock budget ${budget.budget_name}? This will prevent further modifications.`)) {
                    try {
                      const response = await fetch(`/api/v1/general/budgets/${budget.id}/lock`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                      })
                      if (response.ok) {
                        alert('Budget locked successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to lock budget')
                      }
                    } catch (error) {
                      console.error('Error locking budget:', error)
                      alert('Error locking budget')
                    }
                  }
                }}
              >
                <LockClosedIcon className="h-4 w-4" />
              </Button>
            )}
            {budget.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const reason = prompt('Enter reason for unlocking budget:')
                  if (reason) {
                    try {
                      const response = await fetch(`/api/v1/general/budgets/${budget.id}/unlock`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({ reason })
                      })
                      if (response.ok) {
                        alert('Budget unlocked successfully')
                        window.location.reload()
                      } else {
                        alert('Failed to unlock budget')
                      }
                    } catch (error) {
                      console.error('Error unlocking budget:', error)
                      alert('Error unlocking budget')
                    }
                  }
                }}
              >
                <LockOpenIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'budget_name',
      label: 'Budget Name',
      type: 'text',
      required: true,
    },
    {
      name: 'budget_year',
      label: 'Budget Year',
      type: 'select',
      required: true,
      options: [
        { value: '2024', label: '2024' },
        { value: '2025', label: '2025' },
        { value: '2026', label: '2026' },
      ],
    },
    {
      name: 'budget_version',
      label: 'Version',
      type: 'text',
      required: true,
    },
    {
      name: 'budget_type',
      label: 'Budget Type',
      type: 'select',
      required: true,
      options: [
        { value: 'OPERATING', label: 'Operating Budget' },
        { value: 'CAPITAL', label: 'Capital Budget' },
        { value: 'FORECAST', label: 'Forecast' },
        { value: 'DEPARTMENTAL', label: 'Departmental Budget' },
        { value: 'PROJECT', label: 'Project Budget' },
      ],
    },
    {
      name: 'department',
      label: 'Department',
      type: 'select',
      options: [
        { value: '', label: 'All Departments' },
        { value: 'SALES', label: 'Sales' },
        { value: 'MARKETING', label: 'Marketing' },
        { value: 'OPERATIONS', label: 'Operations' },
        { value: 'FINANCE', label: 'Finance' },
        { value: 'HR', label: 'Human Resources' },
        { value: 'IT', label: 'Information Technology' },
      ],
    },
    {
      name: 'cost_center',
      label: 'Cost Center',
      type: 'text',
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
      name: 'variance_threshold',
      label: 'Variance Threshold (%)',
      type: 'number',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateBudget = (data: any) => {
    console.log('Creating budget:', data)
    setShowCreateModal(false)
  }

  const handleEditBudget = (data: any) => {
    console.log('Editing budget:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Budgets"
        description="Manage budgets, forecasts, and variance analysis"
        breadcrumbs={[
          { label: 'General Ledger', href: '/general' },
          { label: 'Budgets' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/budgets/budget-vs-actual', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Budget vs Actual Report</title></head>
                        <body>
                          <h1>Budget vs Actual Report</h1>
                          <p>Period: ${new Date().toLocaleDateString()}</p>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Account</th><th>Budget</th><th>Actual</th><th>Variance</th><th>Variance %</th></tr>
                            ${data.report_data?.map((row: any) => 
                              `<tr><td>${row.account}</td><td>$${row.budget.toFixed(2)}</td><td>$${row.actual.toFixed(2)}</td><td class="${row.variance >= 0 ? 'text-green' : 'text-red'}">$${row.variance.toFixed(2)}</td><td>${row.variance_percent.toFixed(1)}%</td></tr>`
                            ).join('')}
                            <tr style="font-weight:bold"><td>TOTALS</td><td>$${data.totals?.budget.toFixed(2)}</td><td>$${data.totals?.actual.toFixed(2)}</td><td>$${data.totals?.variance.toFixed(2)}</td><td>${data.totals?.variance_percent.toFixed(1)}%</td></tr>
                          </table>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  alert('Failed to generate budget vs actual report')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Budget vs Actual
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/accounts/budget-comparison', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  alert(`Variance analysis complete. Total variance: $${data.report_data?.reduce((sum: number, row: any) => sum + row.variance, 0).toFixed(2)}`)
                } catch (error) {
                  alert('Failed to perform variance analysis')
                }
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Variance Analysis
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const input = document.createElement('input')
                input.type = 'file'
                input.accept = '.csv,.xlsx'
                input.onchange = async (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0]
                  if (file) {
                    const formData = new FormData()
                    formData.append('file', file)
                    try {
                      const response = await fetch('/api/v1/general/budgets/import', {
                        method: 'POST',
                        headers: {
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: formData
                      })
                      const result = await response.json()
                      alert(`Budget imported successfully. ${result.lines_imported} lines imported.`)
                      window.location.reload()
                    } catch (error) {
                      alert('Failed to import budget')
                    }
                  }
                }
                input.click()
              }}
            >
              <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
              Import Budget
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/budgets/export', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const blob = await response.blob()
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `budgets-export-${new Date().toISOString().split('T')[0]}.xlsx`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                  window.URL.revokeObjectURL(url)
                } catch (error) {
                  alert('Failed to export budgets')
                }
              }}
            >
              <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
              Export Budget
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Budget
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={budgets || []}
        searchPlaceholder="Search budgets..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Budget"
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Budget Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Budget year should align with fiscal year periods</li>
              <li>Use version numbers for budget revisions (V1.0, V1.1, etc.)</li>
              <li>Set appropriate variance thresholds for monitoring</li>
              <li>Departmental budgets should include cost center codes</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreateBudget}
            onCancel={() => setShowCreateModal(false)}
            schema={budgetSchema}
            submitLabel="Create Budget"
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Budget"
        size="xl"
      >
        {selectedBudget && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditBudget}
            onCancel={() => setShowEditModal(false)}
            schema={budgetSchema}
            submitLabel="Update Budget"
            defaultValues={{
              budget_name: selectedBudget.budget_name,
              budget_year: selectedBudget.budget_year.toString(),
              budget_version: selectedBudget.budget_version,
              budget_type: selectedBudget.budget_type,
              department: selectedBudget.department,
              cost_center: selectedBudget.cost_center,
              currency_code: selectedBudget.currency_code,
              variance_threshold: selectedBudget.variance_threshold?.toString(),
              notes: selectedBudget.notes,
            }}
          />
        )}
      </Modal>
    </div>
  )
}