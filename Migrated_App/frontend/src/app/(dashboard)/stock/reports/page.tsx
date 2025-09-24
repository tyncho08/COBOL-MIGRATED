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
  ClipboardDocumentListIcon,
  ArchiveBoxIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { apiRequest } from '@/lib/utils/api'

// Types
interface StockReport {
  id: number
  report_type: string
  report_name: string
  description: string
  last_run?: string
  last_run_by?: string
  parameters?: string
  output_format: string
  is_scheduled: boolean
  schedule_frequency?: string
  next_run?: string
  record_count?: number
  file_size?: string
  status: string
}

// Schema
const reportParametersSchema = z.object({
  report_type: z.string().min(1, 'Report type is required'),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  location: z.string().optional(),
  category: z.string().optional(),
  supplier: z.string().optional(),
  include_zero_stock: z.boolean().optional(),
  include_inactive: z.boolean().optional(),
  output_format: z.string().min(1, 'Output format is required'),
})

// Mock data
const mockStockReports: StockReport[] = [
  {
    id: 1,
    report_type: 'STOCK_VALUATION',
    report_name: 'Stock Valuation Report',
    description: 'Current stock values by location and category',
    last_run: '2024-01-15T09:30:00Z',
    last_run_by: 'Manager',
    parameters: 'All locations, Current date',
    output_format: 'PDF',
    is_scheduled: true,
    schedule_frequency: 'MONTHLY',
    next_run: '2024-02-15T09:30:00Z',
    record_count: 1250,
    file_size: '2.1 MB',
    status: 'COMPLETED',
  },
  {
    id: 2,
    report_type: 'STOCK_AGING',
    report_name: 'Stock Aging Analysis',
    description: 'Age analysis of stock items by last movement date',
    last_run: '2024-01-10T14:00:00Z',
    last_run_by: 'John Smith',
    parameters: 'Warehouse A, 90+ days',
    output_format: 'EXCEL',
    is_scheduled: false,
    record_count: 315,
    file_size: '850 KB',
    status: 'COMPLETED',
  },
  {
    id: 3,
    report_type: 'SLOW_MOVING',
    report_name: 'Slow Moving Items',
    description: 'Items with low turnover or no movement',
    last_run: '2024-01-12T11:15:00Z',
    last_run_by: 'Jane Doe',
    parameters: 'All locations, 6 month period',
    output_format: 'CSV',
    is_scheduled: true,
    schedule_frequency: 'QUARTERLY',
    next_run: '2024-04-12T11:15:00Z',
    record_count: 89,
    file_size: '125 KB',
    status: 'COMPLETED',
  },
  {
    id: 4,
    report_type: 'REORDER_LEVELS',
    report_name: 'Reorder Level Analysis',
    description: 'Items below reorder levels requiring attention',
    last_run: '2024-01-16T08:00:00Z',
    last_run_by: 'Bob Johnson',
    parameters: 'All active items',
    output_format: 'PDF',
    is_scheduled: true,
    schedule_frequency: 'WEEKLY',
    next_run: '2024-01-23T08:00:00Z',
    record_count: 45,
    file_size: '320 KB',
    status: 'RUNNING',
  },
  {
    id: 5,
    report_type: 'ABC_ANALYSIS',
    report_name: 'ABC Classification',
    description: 'ABC analysis based on value and movement',
    last_run: '2024-01-01T00:00:00Z',
    last_run_by: 'System',
    parameters: 'Annual analysis, All items',
    output_format: 'EXCEL',
    is_scheduled: true,
    schedule_frequency: 'YEARLY',
    next_run: '2025-01-01T00:00:00Z',
    record_count: 2150,
    file_size: '5.8 MB',
    status: 'COMPLETED',
  },
  {
    id: 6,
    report_type: 'NEGATIVE_STOCK',
    report_name: 'Negative Stock Report',
    description: 'Items with negative stock quantities',
    status: 'FAILED',
    output_format: 'PDF',
    is_scheduled: false,
    record_count: 0,
  },
]

const getReportTypeBadge = (type: string) => {
  switch (type) {
    case 'STOCK_VALUATION':
      return <Badge variant="info">Valuation</Badge>
    case 'STOCK_AGING':
      return <Badge variant="warning">Aging</Badge>
    case 'SLOW_MOVING':
      return <Badge variant="default">Slow Moving</Badge>
    case 'REORDER_LEVELS':
      return <Badge variant="danger">Reorder</Badge>
    case 'ABC_ANALYSIS':
      return <Badge variant="success">ABC Analysis</Badge>
    case 'NEGATIVE_STOCK':
      return <Badge variant="danger">Negative Stock</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
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

export default function StockReportsPage() {
  const [showRunModal, setShowRunModal] = useState(false)
  const [selectedReport, setSelectedReport] = useState<StockReport | null>(null)

  const { data: stockReports, isLoading } = useQuery({
    queryKey: ['stock-reports'],
    queryFn: async () => {
      const response = await apiRequest('/api/v1/stock/reports')
      if (!response.ok) {
        throw new Error(`Failed to fetch stock reports: ${response.statusText}`)
      }
      const result = await response.json()
      return result.data || []
    }
  })

  const columns: ColumnDef<StockReport>[] = [
    {
      accessorKey: 'report_type',
      header: 'Type',
      cell: ({ row }) => {
        return getReportTypeBadge(row.getValue('report_type'))
      },
    },
    {
      accessorKey: 'report_name',
      header: 'Report Name',
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
      accessorKey: 'record_count',
      header: 'Records',
      cell: ({ row }) => {
        const count = row.getValue('record_count') as number
        return count ? count.toLocaleString() : '-'
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
                // Handle view report
              }}
              disabled={!report.last_run}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle schedule report
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
        { value: 'STOCK_VALUATION', label: 'Stock Valuation Report' },
        { value: 'STOCK_AGING', label: 'Stock Aging Analysis' },
        { value: 'SLOW_MOVING', label: 'Slow Moving Items' },
        { value: 'REORDER_LEVELS', label: 'Reorder Level Analysis' },
        { value: 'ABC_ANALYSIS', label: 'ABC Classification' },
        { value: 'NEGATIVE_STOCK', label: 'Negative Stock Report' },
        { value: 'STOCK_MOVEMENT', label: 'Stock Movement Summary' },
        { value: 'TURNOVER_ANALYSIS', label: 'Stock Turnover Analysis' },
      ],
    },
    {
      name: 'date_from',
      label: 'Date From',
      type: 'date',
    },
    {
      name: 'date_to',
      label: 'Date To',
      type: 'date',
    },
    {
      name: 'location',
      label: 'Location',
      type: 'select',
      options: [
        { value: '', label: 'All Locations' },
        { value: 'WAREHOUSE-A', label: 'Warehouse A' },
        { value: 'WAREHOUSE-B', label: 'Warehouse B' },
        { value: 'SHOP-FLOOR', label: 'Shop Floor' },
        { value: 'RETURNS', label: 'Returns Area' },
      ],
    },
    {
      name: 'category',
      label: 'Category',
      type: 'select',
      options: [
        { value: '', label: 'All Categories' },
        { value: 'ELECTRONICS', label: 'Electronics' },
        { value: 'HARDWARE', label: 'Hardware' },
        { value: 'SOFTWARE', label: 'Software' },
        { value: 'ACCESSORIES', label: 'Accessories' },
      ],
    },
    {
      name: 'supplier',
      label: 'Supplier',
      type: 'select',
      options: [
        { value: '', label: 'All Suppliers' },
        { value: 'SUPP001', label: 'ABC Supplies Ltd' },
        { value: 'SUPP002', label: 'Tech Components Inc' },
        { value: 'SUPP003', label: 'Office Supplies Co' },
      ],
    },
    {
      name: 'include_zero_stock',
      label: 'Include Zero Stock Items',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'include_inactive',
      label: 'Include Inactive Items',
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
    console.log('Running report with parameters:', data)
    setShowRunModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Stock Reports"
        description="Generate and manage stock analysis and reporting"
        breadcrumbs={[
          { label: 'Stock Control', href: '/stock' },
          { label: 'Stock Reports' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle dashboard
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Stock Dashboard
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle exception report
              }}
            >
              <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
              Exception Report
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                const summaryWindow = window.open('', '_blank')
                if (summaryWindow) {
                  summaryWindow.document.write(`
                    <html>
                      <head><title>Stock Summary Report</title></head>
                      <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h1>Stock Summary Report</h1>
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                          <tr style="background: #f3f4f6;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Category</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Items</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Total Qty</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Total Value</th>
                          </tr>
                          <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;">Electronics</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">245</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">1,890</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$185,420.00</td>
                          </tr>
                          <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;">Hardware</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">512</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">15,420</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$125,300.50</td>
                          </tr>
                          <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;">Software</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">128</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">850</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$89,500.00</td>
                          </tr>
                          <tr style="background: #e5e7eb; font-weight: bold;">
                            <td style="padding: 10px; border: 1px solid #ddd;">Total</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">885</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">18,160</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">$400,220.50</td>
                          </tr>
                        </table>
                        <p style="margin-top: 40px; color: #666;">Generated: ${new Date().toLocaleString()}</p>
                      </body>
                    </html>
                  `)
                }
              }}
            >
              <ArchiveBoxIcon className="h-4 w-4 mr-2" />
              Stock Summary
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
        data={stockReports || []}
        searchPlaceholder="Search reports..."
      />

      {/* Run Report Modal */}
      <Modal
        isOpen={showRunModal}
        onClose={() => setShowRunModal(false)}
        title="Run Stock Report"
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Report Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Date ranges are optional - defaults to current period</li>
              <li>Large reports may take several minutes to generate</li>
              <li>Reports are automatically saved with timestamp</li>
              <li>Check your email for completion notification</li>
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
              output_format: selectedReport.output_format,
            } : {}}
          />
        </div>
      </Modal>
    </div>
  )
}