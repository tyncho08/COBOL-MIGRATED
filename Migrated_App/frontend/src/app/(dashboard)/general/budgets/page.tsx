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

// Mock data
const mockBudgets: Budget[] = [
  {
    id: 1,
    budget_name: 'Annual Operating Budget 2024',
    budget_year: 2024,
    budget_version: 'V1.0',
    budget_type: 'OPERATING',
    department: 'ALL',
    currency_code: 'USD',
    status: 'APPROVED',
    created_by: 'Budget Manager',
    created_date: '2023-12-01T09:00:00Z',
    approved_by: 'CFO',
    approved_date: '2023-12-15T16:30:00Z',
    locked_by: 'CFO',
    locked_date: '2024-01-01T00:00:00Z',
    total_revenue: 2500000.00,
    total_expenses: 2200000.00,
    net_income: 300000.00,
    variance_threshold: 5.0,
    is_active: true,
    notes: 'Board approved budget for fiscal year 2024',
  },
  {
    id: 2,
    budget_name: 'Capital Expenditure Budget 2024',
    budget_year: 2024,
    budget_version: 'V2.1',
    budget_type: 'CAPITAL',
    currency_code: 'USD',
    status: 'APPROVED',
    created_by: 'Finance Director',
    created_date: '2023-11-15T14:20:00Z',
    approved_by: 'Board',
    approved_date: '2023-12-20T10:00:00Z',
    total_revenue: 0.00,
    total_expenses: 450000.00,
    net_income: -450000.00,
    variance_threshold: 10.0,
    is_active: true,
    notes: 'Equipment and facility upgrades',
  },
  {
    id: 3,
    budget_name: 'Q1 2024 Revised Forecast',
    budget_year: 2024,
    budget_version: 'V1.2',
    budget_type: 'FORECAST',
    department: 'SALES',
    currency_code: 'USD',
    status: 'DRAFT',
    created_by: 'Sales Manager',
    created_date: '2024-01-15T11:30:00Z',
    total_revenue: 650000.00,
    total_expenses: 580000.00,
    net_income: 70000.00,
    variance_threshold: 3.0,
    is_active: false,
    notes: 'Quarterly forecast revision based on market conditions',
  },
  {
    id: 4,
    budget_name: 'Department Budget - Marketing',
    budget_year: 2024,
    budget_version: 'V1.0',
    budget_type: 'DEPARTMENTAL',
    department: 'MARKETING',
    cost_center: 'MKT001',
    currency_code: 'USD',
    status: 'PENDING',
    created_by: 'Marketing Director',
    created_date: '2024-01-10T13:45:00Z',
    total_revenue: 0.00,
    total_expenses: 180000.00,
    net_income: -180000.00,
    variance_threshold: 5.0,
    is_active: false,
    notes: 'Annual marketing department budget proposal',
  },
]

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
    queryFn: () => Promise.resolve(mockBudgets),
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
                // Handle view budget details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle copy budget
              }}
            >
              <DocumentDuplicateIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle variance analysis
              }}
            >
              <ChartBarIcon className="h-4 w-4" />
            </Button>
            {budget.status === 'APPROVED' && !budget.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle lock budget
                }}
              >
                <LockClosedIcon className="h-4 w-4" />
              </Button>
            )}
            {budget.locked_by && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle unlock budget
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
              onClick={() => {
                // Handle budget vs actual report
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Budget vs Actual
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle variance analysis
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Variance Analysis
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle import budget
              }}
            >
              <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
              Import Budget
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle export budget
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