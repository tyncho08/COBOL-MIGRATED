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
  DocumentTextIcon, 
  ChartBarIcon, 
  PrinterIcon, 
  EyeIcon,
  CalculatorIcon,
  DocumentChartBarIcon,
  CurrencyDollarIcon,
  ScaleIcon,
  ClipboardDocumentListIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface FinancialReport {
  id: number
  report_type: string
  report_name: string
  description: string
  category: string
  last_run?: string
  last_run_by?: string
  parameters?: string
  output_format: string
  is_scheduled: boolean
  schedule_frequency?: string
  next_run?: string
  status: string
  period_from?: string
  period_to?: string
  file_size?: string
}

// Schema
const reportParametersSchema = z.object({
  report_type: z.string().min(1, 'Report type is required'),
  period_from: z.string().min(1, 'From period is required'),
  period_to: z.string().min(1, 'To period is required'),
  year: z.string().min(1, 'Year is required'),
  include_budget: z.boolean().optional(),
  include_prior_year: z.boolean().optional(),
  detail_level: z.string().min(1, 'Detail level is required'),
  output_format: z.string().min(1, 'Output format is required'),
  consolidate_entities: z.boolean().optional(),
})

// Mock data
const mockFinancialReports: FinancialReport[] = [
  {
    id: 1,
    report_type: 'TRIAL_BALANCE',
    report_name: 'Trial Balance',
    description: 'Detailed trial balance with account balances',
    category: 'STATUTORY',
    last_run: '2024-01-15T16:30:00Z',
    last_run_by: 'Manager',
    parameters: 'Period 1-12/2024, Detail Level 3',
    output_format: 'PDF',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-15T16:30:00Z',
    status: 'COMPLETED',
    period_from: '1',
    period_to: '12',
    file_size: '1.5 MB',
  },
  {
    id: 2,
    report_type: 'BALANCE_SHEET',
    report_name: 'Balance Sheet',
    description: 'Statement of financial position',
    category: 'FINANCIAL_STATEMENTS',
    last_run: '2024-01-31T18:00:00Z',
    last_run_by: 'CFO',
    parameters: 'YTD 2024, With Budget Comparison',
    output_format: 'EXCEL',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-29T18:00:00Z',
    status: 'COMPLETED',
    period_from: '1',
    period_to: '1',
    file_size: '850 KB',
  },
  {
    id: 3,
    report_type: 'INCOME_STATEMENT',
    report_name: 'Income Statement',
    description: 'Profit & Loss statement',
    category: 'FINANCIAL_STATEMENTS',
    last_run: '2024-01-31T18:00:00Z',
    last_run_by: 'CFO',
    parameters: 'YTD 2024, With Prior Year',
    output_format: 'PDF',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-29T18:00:00Z',
    status: 'COMPLETED',
    period_from: '1',
    period_to: '1',
    file_size: '720 KB',
  },
  {
    id: 4,
    report_type: 'CASH_FLOW',
    report_name: 'Cash Flow Statement',
    description: 'Statement of cash flows',
    category: 'FINANCIAL_STATEMENTS',
    last_run: '2024-01-31T18:00:00Z',
    last_run_by: 'CFO',
    parameters: 'YTD 2024, Direct Method',
    output_format: 'PDF',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-29T18:00:00Z',
    status: 'COMPLETED',
    period_from: '1',
    period_to: '1',
    file_size: '650 KB',
  },
  {
    id: 5,
    report_type: 'GENERAL_LEDGER',
    report_name: 'General Ledger Detail',
    description: 'Detailed general ledger transactions',
    category: 'TRANSACTION_REPORTS',
    last_run: '2024-01-20T14:00:00Z',
    last_run_by: 'Accountant',
    parameters: 'All accounts, Period 1/2024',
    output_format: 'CSV',
    is_scheduled: false,
    status: 'COMPLETED',
    period_from: '1',
    period_to: '1',
    file_size: '8.2 MB',
  },
  {
    id: 6,
    report_type: 'BUDGET_VARIANCE',
    report_name: 'Budget Variance Analysis',
    description: 'Actual vs budget variance report',
    category: 'MANAGEMENT_REPORTS',
    last_run: '2024-01-25T10:30:00Z',
    last_run_by: 'Controller',
    parameters: 'YTD 2024, All departments',
    output_format: 'EXCEL',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-25T10:30:00Z',
    status: 'COMPLETED',
    period_from: '1',
    period_to: '1',
    file_size: '2.1 MB',
  },
  {
    id: 7,
    report_type: 'AGING_SUMMARY',
    report_name: 'Account Aging Summary',
    description: 'AR/AP aging analysis summary',
    category: 'MANAGEMENT_REPORTS',
    status: 'RUNNING',
    output_format: 'PDF',
    is_scheduled: false,
  },
]

const getReportTypeBadge = (type: string) => {
  switch (type) {
    case 'TRIAL_BALANCE':
      return <Badge variant="info">Trial Balance</Badge>
    case 'BALANCE_SHEET':
      return <Badge variant="success">Balance Sheet</Badge>
    case 'INCOME_STATEMENT':
      return <Badge variant="warning">Income Statement</Badge>
    case 'CASH_FLOW':
      return <Badge variant="default">Cash Flow</Badge>
    case 'GENERAL_LEDGER':
      return <Badge variant="default">General Ledger</Badge>
    case 'BUDGET_VARIANCE':
      return <Badge variant="info">Budget Variance</Badge>
    case 'AGING_SUMMARY':
      return <Badge variant="warning">Aging Summary</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getCategoryBadge = (category: string) => {
  switch (category) {
    case 'FINANCIAL_STATEMENTS':
      return <Badge variant="success" className="text-xs">Financial</Badge>
    case 'STATUTORY':
      return <Badge variant="info" className="text-xs">Statutory</Badge>
    case 'MANAGEMENT_REPORTS':
      return <Badge variant="warning" className="text-xs">Management</Badge>
    case 'TRANSACTION_REPORTS':
      return <Badge variant="default" className="text-xs">Transaction</Badge>
    case 'REGULATORY':
      return <Badge variant="danger" className="text-xs">Regulatory</Badge>
    default:
      return <Badge variant="default" className="text-xs">{category}</Badge>
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return <Badge variant="success">Completed</Badge>
    case 'RUNNING':
      return <Badge variant="warning">Running</Badge>
    case 'FAILED':
      return <Badge variant="danger">Failed</Badge>
    case 'SCHEDULED':
      return <Badge variant="info">Scheduled</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function FinancialReportsPage() {
  const [showRunModal, setShowRunModal] = useState(false)
  const [selectedReport, setSelectedReport] = useState<FinancialReport | null>(null)

  const { data: financialReports, isLoading } = useQuery({
    queryKey: ['financial-reports'],
    queryFn: () => Promise.resolve(mockFinancialReports),
  })

  const columns: ColumnDef<FinancialReport>[] = [
    {
      accessorKey: 'report_type',
      header: 'Report Type',
      cell: ({ row }) => {
        return getReportTypeBadge(row.getValue('report_type'))
      },
    },
    {
      accessorKey: 'report_name',
      header: 'Report Name',
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ row }) => {
        return getCategoryBadge(row.getValue('category'))
      },
    },
    {
      accessorKey: 'description',
      header: 'Description',
      cell: ({ row }) => {
        const description = row.getValue('description') as string
        return (
          <span className="max-w-xs truncate" title={description}>
            {description}
          </span>
        )
      },
    },
    {
      accessorKey: 'last_run',
      header: 'Last Run',
      cell: ({ row }) => {
        const lastRun = row.getValue('last_run') as string
        return lastRun ? new Date(lastRun).toLocaleString() : 'Never'
      },
    },
    {
      accessorKey: 'last_run_by',
      header: 'Run By',
    },
    {
      accessorKey: 'period_from',
      header: 'Period Range',
      cell: ({ row }) => {
        const report = row.original
        if (report.period_from && report.period_to) {
          return `${report.period_from}-${report.period_to}`
        }
        return '-'
      },
    },
    {
      accessorKey: 'file_size',
      header: 'File Size',
    },
    {
      accessorKey: 'output_format',
      header: 'Format',
      cell: ({ row }) => {
        const format = row.getValue('output_format') as string
        return <Badge variant="default">{format}</Badge>
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        return getStatusBadge(row.getValue('status'))
      },
    },
    {
      id: 'schedule',
      header: 'Schedule',
      cell: ({ row }) => {
        const report = row.original
        if (!report.is_scheduled) {
          return <span className="text-gray-400">Manual</span>
        }
        return (
          <div className="text-sm">
            <div>{report.schedule_frequency}</div>
            {report.next_run && (
              <div className="text-xs text-gray-500">
                Next: {new Date(report.next_run).toLocaleDateString()}
              </div>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const report = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedReport(report)
                setShowRunModal(true)
              }}
              disabled={report.status === 'RUNNING'}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const modal = document.createElement('div')
                modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000'
                modal.innerHTML = `
                  <div style="background:white;padding:2rem;border-radius:8px;max-width:800px;width:90%;max-height:80vh;overflow-y:auto">
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">${report.name}</h2>
                    <p style="margin-bottom:1rem">${report.description}</p>
                    <div style="background:#f3f4f6;padding:1rem;border-radius:4px">
                      <p><strong>Type:</strong> ${report.report_type}</p>
                      <p><strong>Category:</strong> ${report.category}</p>
                      <p><strong>Format:</strong> ${report.output_format}</p>
                      <p><strong>Frequency:</strong> ${report.frequency || 'On-demand'}</p>
                      <p><strong>Last Run:</strong> ${report.last_run ? new Date(report.last_run).toLocaleString() : 'Never'}</p>
                    </div>
                    ${report.report_type === 'TRIAL_BALANCE' ? `
                      <div style="margin-top:1rem">
                        <h3 style="font-weight:bold">Quick Preview:</h3>
                        <p>Total Debits: $87,500.00</p>
                        <p>Total Credits: $87,500.00</p>
                        <p style="color:green">✓ In Balance</p>
                      </div>
                    ` : ''}
                    <button style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;margin-top:1rem" onclick="this.parentElement.parentElement.remove()">Close</button>
                  </div>
                `
                document.body.appendChild(modal)
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
              disabled={!report.last_run}
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
                    <h2 style="font-size:1.5rem;font-weight:bold;margin-bottom:1rem">Schedule Report: ${report.name}</h2>
                    <form id="scheduleForm">
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Frequency:</label>
                        <select name="frequency" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" required>
                          <option value="daily">Daily</option>
                          <option value="weekly">Weekly</option>
                          <option value="monthly">Monthly</option>
                          <option value="quarterly">Quarterly</option>
                          <option value="yearly">Yearly</option>
                        </select>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Time:</label>
                        <input type="time" name="time" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" value="08:00" required>
                      </div>
                      <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.25rem">Email To:</label>
                        <input type="email" name="email" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px" placeholder="finance@company.com" required>
                      </div>
                      <div style="display:flex;gap:0.5rem">
                        <button type="submit" style="background:#3b82f6;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer">Schedule</button>
                        <button type="button" style="background:#6b7280;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">Cancel</button>
                      </div>
                    </form>
                  </div>
                `
                document.body.appendChild(modal)
                modal.querySelector('#scheduleForm').onsubmit = (e) => {
                  e.preventDefault()
                  const formData = new FormData(e.target)
                  alert(`Report scheduled: ${formData.get('frequency')} at ${formData.get('time')} to ${formData.get('email')}`)
                  modal.remove()
                }
                modal.onclick = (e) => {
                  if (e.target === modal) modal.remove()
                }
              }}
            >
              <ClipboardDocumentListIcon className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  const reportParameterFields: FormField[] = [
    {
      name: 'report_type',
      label: 'Report Type',
      type: 'select',
      required: true,
      options: [
        { value: 'TRIAL_BALANCE', label: 'Trial Balance' },
        { value: 'BALANCE_SHEET', label: 'Balance Sheet' },
        { value: 'INCOME_STATEMENT', label: 'Income Statement' },
        { value: 'CASH_FLOW', label: 'Cash Flow Statement' },
        { value: 'GENERAL_LEDGER', label: 'General Ledger Detail' },
        { value: 'BUDGET_VARIANCE', label: 'Budget Variance Analysis' },
        { value: 'AGING_SUMMARY', label: 'Account Aging Summary' },
        { value: 'ACCOUNT_ACTIVITY', label: 'Account Activity Report' },
      ],
    },
    {
      name: 'period_from',
      label: 'From Period',
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
      ],
    },
    {
      name: 'period_to',
      label: 'To Period',
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
      ],
    },
    {
      name: 'year',
      label: 'Year',
      type: 'select',
      required: true,
      options: [
        { value: '2024', label: '2024' },
        { value: '2023', label: '2023' },
        { value: '2022', label: '2022' },
      ],
    },
    {
      name: 'detail_level',
      label: 'Detail Level',
      type: 'select',
      required: true,
      options: [
        { value: '1', label: 'Summary Only' },
        { value: '2', label: 'Account Level' },
        { value: '3', label: 'Sub-Account Level' },
        { value: '4', label: 'Full Detail' },
      ],
    },
    {
      name: 'include_budget',
      label: 'Include Budget Comparison',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'include_prior_year',
      label: 'Include Prior Year Comparison',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'consolidate_entities',
      label: 'Consolidate Entities',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'output_format',
      label: 'Output Format',
      type: 'select',
      required: true,
      options: [
        { value: 'PDF', label: 'PDF Document' },
        { value: 'EXCEL', label: 'Excel Spreadsheet' },
        { value: 'CSV', label: 'CSV File' },
        { value: 'PRINT', label: 'Print to Printer' },
      ],
    },
  ]

  const handleRunReport = (data: any) => {
    console.log('Running financial report with parameters:', data)
    setShowRunModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Financial Reports"
        description="Generate and manage financial statements and analysis reports"
        breadcrumbs={[
          { label: 'General Ledger', href: '/general' },
          { label: 'Financial Reports' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  window.location.href = '/general/dashboard'
                } catch (error) {
                  alert('Failed to navigate to financial dashboard')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Financial Dashboard
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/journals/trial-balance', {
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                  })
                  const data = await response.json()
                  const reportWindow = window.open('', '_blank')
                  if (reportWindow) {
                    reportWindow.document.write(`
                      <html>
                        <head><title>Trial Balance</title></head>
                        <body>
                          <h1>Trial Balance</h1>
                          <p>Period: ${new Date().toLocaleDateString()}</p>
                          <table border="1" style="border-collapse:collapse">
                            <tr><th>Account Code</th><th>Account Name</th><th>Debit</th><th>Credit</th></tr>
                            ${data.trial_balance?.map((row: any) => 
                              `<tr><td>${row.account_code}</td><td>${row.account_name}</td><td>${row.debit > 0 ? '$' + row.debit.toFixed(2) : ''}</td><td>${row.credit > 0 ? '$' + row.credit.toFixed(2) : ''}</td></tr>`
                            ).join('')}
                            <tr style="font-weight:bold"><td colspan="2">TOTALS</td><td>$${data.total_debits?.toFixed(2)}</td><td>$${data.total_credits?.toFixed(2)}</td></tr>
                          </table>
                          <p>${data.total_debits === data.total_credits ? 'Trial balance is in balance' : 'WARNING: Trial balance is OUT OF BALANCE'}</p>
                          <p>Generated: ${new Date().toLocaleString()}</p>
                        </body>
                      </html>
                    `)
                  }
                } catch (error) {
                  alert('Failed to generate trial balance')
                }
              }}
            >
              <ScaleIcon className="h-4 w-4 mr-2" />
              Trial Balance
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/reports/month-end-package', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({ period: 1, year: 2024 })
                  })
                  const result = await response.json()
                  alert(`Month End Package generated with ${result.reports_count} reports. Check your downloads folder.`)
                } catch (error) {
                  alert('Failed to generate month end package')
                }
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Month End Package
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/general/reports/financial-statements', {
                    method: 'POST', 
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({ period: 1, year: 2024, include_notes: true })
                  })
                  const blob = await response.blob()
                  const url = window.URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = `financial-statements-${new Date().toISOString().split('T')[0]}.pdf`
                  document.body.appendChild(link)
                  link.click()
                  document.body.removeChild(link)
                  window.URL.revokeObjectURL(url)
                } catch (error) {
                  alert('Failed to generate financial statements')
                }
              }}
            >
              <DocumentChartBarIcon className="h-4 w-4 mr-2" />
              Financial Statements
            </Button>
            <Button onClick={() => setShowRunModal(true)}>
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Run Report
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={financialReports || []}
        searchPlaceholder="Search financial reports..."
      />

      {/* Run Report Modal */}
      <Modal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        title="Run Financial Report"
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Report Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Ensure period is closed before running final reports</li>
              <li>Financial statements require balanced trial balance</li>
              <li>Budget comparisons require active budget data</li>
              <li>Large reports may take several minutes to generate</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={reportParameterFields}
            onSubmit={handleRunReport}
            onCancel={() => setShowRunModal(false)}
            schema={reportParametersSchema}
            submitLabel="Run Report"
            defaultValues={selectedReport ? {
              report_type: selectedReport.report_type,
              period_from: selectedReport.period_from || '1',
              period_to: selectedReport.period_to || '1',
              year: '2024',
              detail_level: '2',
              output_format: selectedReport.output_format,
            } : {
              period_from: '1',
              period_to: '1',
              year: '2024',
              detail_level: '2',
              output_format: 'PDF',
            }}
          />
        </div>
      </Modal>
    </div>
  )
}