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
  TrashIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FolderIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { ChartOfAccount, chartOfAccountsApi } from '@/lib/api/chart-of-accounts'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

// Schema
const accountSchema = z.object({
  account_code: z.string()
    .min(1, 'Account code is required')
    .regex(/^\d{4}\.\d{4}$/, 'Account code must be in format ####.####'),
  account_name: z.string().min(1, 'Account name is required'),
  account_type: z.string().min(1, 'Account type is required'),
  parent_account_id: z.string().optional(),
  is_header: z.string(),
  allow_posting: z.string(),
  budget_enabled: z.string(),
  is_active: z.string(),
  tax_code: z.string().optional(),
  analysis_required: z.string(),
  currency_code: z.string().optional(),
  notes: z.string().optional(),
})

const getAccountTypeBadge = (type: string) => {
  switch (type) {
    case 'ASSET':
      return <Badge variant="success">Asset</Badge>
    case 'LIABILITY':
      return <Badge variant="danger">Liability</Badge>
    case 'INCOME':
      return <Badge variant="info">Income</Badge>
    case 'EXPENSE':
      return <Badge variant="warning">Expense</Badge>
    case 'CAPITAL':
      return <Badge variant="default">Capital</Badge>
    case 'CONTROL':
      return <Badge variant="default">Control</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getAccountTypeIcon = (type: string) => {
  switch (type) {
    case 'ASSET':
      return <BanknotesIcon className="h-4 w-4 text-green-500" />
    case 'LIABILITY':
      return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
    case 'INCOME':
      return <ArrowTrendingUpIcon className="h-4 w-4 text-blue-500" />
    case 'EXPENSE':
      return <ArrowTrendingDownIcon className="h-4 w-4 text-orange-500" />
    case 'CAPITAL':
      return <ChartBarIcon className="h-4 w-4 text-purple-500" />
    default:
      return <FolderIcon className="h-4 w-4 text-gray-500" />
  }
}

export default function ChartOfAccountsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showStatementModal, setShowStatementModal] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<ChartOfAccount | null>(null)
  const [accountToDelete, setAccountToDelete] = useState<ChartOfAccount | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for accounts
  const { data: accounts, isLoading, error } = useQuery({
    queryKey: ['chartOfAccounts'],
    queryFn: () => chartOfAccountsApi.getAll(),
  })

  // Query for parent accounts (for select options)
  const { data: parentAccounts } = useQuery({
    queryKey: ['parentAccounts'],
    queryFn: () => chartOfAccountsApi.getAll({ active_only: true }),
    select: (data) => Array.isArray(data) ? data.filter((a: any) => a.is_header) : [],
  })

  // Mutation for creating account
  const createMutation = useMutation({
    mutationFn: chartOfAccountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chartOfAccounts'] })
      toast.success('Account created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create account')
    },
  })

  // Mutation for updating account
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ChartOfAccount> }) =>
      chartOfAccountsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chartOfAccounts'] })
      toast.success('Account updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update account')
    },
  })

  // Mutation for deleting account
  const deleteMutation = useMutation({
    mutationFn: chartOfAccountsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chartOfAccounts'] })
      toast.success('Account deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete account')
    },
  })

  // Mutation for toggling active status
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      chartOfAccountsApi.toggleActive(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chartOfAccounts'] })
      toast.success('Account status updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update account status')
    },
  })

  // Build hierarchical structure
  const buildAccountTree = (accounts: ChartOfAccount[]) => {
    const accountMap = new Map<number, ChartOfAccount & { children: ChartOfAccount[] }>()
    const rootAccounts: (ChartOfAccount & { children: ChartOfAccount[] })[] = []

    // First pass: create all nodes
    accounts.forEach(account => {
      accountMap.set(account.id!, { ...account, children: [] })
    })

    // Second pass: build hierarchy
    accounts.forEach(account => {
      const node = accountMap.get(account.id!)!
      if (account.parent_account_id) {
        const parent = accountMap.get(account.parent_account_id)
        if (parent) {
          parent.children.push(node)
        } else {
          rootAccounts.push(node)
        }
      } else {
        rootAccounts.push(node)
      }
    })

    return rootAccounts
  }

  const toggleRowExpanded = (accountCode: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(accountCode)) {
      newExpanded.delete(accountCode)
    } else {
      newExpanded.add(accountCode)
    }
    setExpandedRows(newExpanded)
  }

  const columns: ColumnDef<ChartOfAccount>[] = [
    {
      accessorKey: 'account_code',
      header: 'Account Code',
      cell: ({ row }) => {
        const account = row.original
        const level = account.level || 0
        const code = account.account_code
        const hasChildren = account.is_header
        const isExpanded = expandedRows.has(code)
        
        return (
          <div className="flex items-center" style={{ paddingLeft: `${level * 24}px` }}>
            {hasChildren && (
              <button
                onClick={() => toggleRowExpanded(code)}
                className="mr-2 text-gray-500 hover:text-gray-700"
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            )}
            <div className="flex items-center space-x-2">
              {getAccountTypeIcon(account.account_type)}
              <span className={account.is_header ? 'font-semibold' : ''}>
                {code}
              </span>
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'account_name',
      header: 'Account Name',
      cell: ({ row }) => {
        const isHeader = row.original.is_header
        const name = row.getValue('account_name') as string
        return (
          <span className={isHeader ? 'font-semibold' : ''}>
            {name}
          </span>
        )
      },
    },
    {
      accessorKey: 'account_type',
      header: 'Type',
      cell: ({ row }) => {
        return getAccountTypeBadge(row.getValue('account_type'))
      },
    },
    {
      accessorKey: 'current_balance',
      header: 'Current Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('current_balance') || '0')
        const type = row.original.account_type
        const isNegative = (type === 'LIABILITY' || type === 'INCOME' || type === 'CAPITAL') && amount < 0
        
        return (
          <span className={isNegative ? 'text-red-600' : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: row.original.currency_code || 'USD',
            }).format(Math.abs(amount))}
            {isNegative && ' CR'}
          </span>
        )
      },
    },
    {
      accessorKey: 'ytd_movement',
      header: 'YTD Movement',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('ytd_movement') || '0')
        return (
          <span className={amount < 0 ? 'text-red-600' : amount > 0 ? 'text-green-600' : ''}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: row.original.currency_code || 'USD',
            }).format(Math.abs(amount))}
          </span>
        )
      },
    },
    {
      accessorKey: 'allow_posting',
      header: 'Posting',
      cell: ({ row }) => {
        const allowPosting = row.getValue('allow_posting') as boolean
        return allowPosting ? (
          <Badge variant="success">Yes</Badge>
        ) : (
          <Badge variant="default">No</Badge>
        )
      },
    },
    {
      accessorKey: 'budget_enabled',
      header: 'Budget',
      cell: ({ row }) => {
        const budgetEnabled = row.original.budget_enabled
        return budgetEnabled ? (
          <Badge variant="info">Yes</Badge>
        ) : (
          <Badge variant="default">No</Badge>
        )
      },
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ row }) => {
        const isActive = row.getValue('is_active') as boolean
        return isActive ? (
          <Badge variant="success">Active</Badge>
        ) : (
          <Badge variant="danger">Inactive</Badge>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const account = row.original
        const isSystemAccount = account.is_system_account
        
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedAccount(account)
                setShowEditModal(true)
              }}
              disabled={isSystemAccount}
              title="Edit"
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedAccount(account)
                setShowStatementModal(true)
              }}
              title="View Statement"
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            {canEdit('general') && !isSystemAccount && (
              <Button
                size="sm"
                variant={account.is_active ? "outline" : "secondary"}
                onClick={() => handleToggleActive(account)}
                title={account.is_active ? "Deactivate" : "Activate"}
              >
                {account.is_active ? "Active" : "Inactive"}
              </Button>
            )}
            {canDelete('general') && !isSystemAccount && !account.is_header && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteAccount(account)}
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
      name: 'account_code',
      label: 'Account Code',
      type: 'text',
      required: true,
      placeholder: '1000.0000',
    },
    {
      name: 'account_name',
      label: 'Account Name',
      type: 'text',
      required: true,
    },
    {
      name: 'account_type',
      label: 'Account Type',
      type: 'select',
      required: true,
      options: [
        { value: 'ASSET', label: 'Asset' },
        { value: 'LIABILITY', label: 'Liability' },
        { value: 'CAPITAL', label: 'Capital' },
        { value: 'INCOME', label: 'Income' },
        { value: 'EXPENSE', label: 'Expense' },
        { value: 'CONTROL', label: 'Control' },
      ],
    },
    {
      name: 'parent_account_id',
      label: 'Parent Account',
      type: 'select',
      options: [
        { value: '', label: 'None (Top Level)' },
        ...(parentAccounts?.map(a => ({ 
          value: a.id!.toString(), 
          label: `${a.account_code} - ${a.account_name}` 
        })) || []),
      ],
    },
    {
      name: 'is_header',
      label: 'Header Account',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'allow_posting',
      label: 'Allow Posting',
      type: 'select',
      options: [
        { value: 'true', label: 'Yes' },
        { value: 'false', label: 'No' },
      ],
    },
    {
      name: 'budget_enabled',
      label: 'Budget Enabled',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'is_active',
      label: 'Active',
      type: 'select',
      options: [
        { value: 'true', label: 'Yes' },
        { value: 'false', label: 'No' },
      ],
    },
    {
      name: 'tax_code',
      label: 'Tax Code',
      type: 'select',
      options: [
        { value: '', label: 'None' },
        { value: 'S', label: 'Standard Rate' },
        { value: 'R', label: 'Reduced Rate' },
        { value: 'Z', label: 'Zero Rated' },
        { value: 'E', label: 'Exempt' },
      ],
    },
    {
      name: 'analysis_required',
      label: 'Analysis Required',
      type: 'select',
      options: [
        { value: 'false', label: 'No' },
        { value: 'true', label: 'Yes' },
      ],
    },
    {
      name: 'currency_code',
      label: 'Currency',
      type: 'select',
      options: [
        { value: '', label: 'Default (USD)' },
        { value: 'USD', label: 'US Dollar' },
        { value: 'EUR', label: 'Euro' },
        { value: 'GBP', label: 'British Pound' },
      ],
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateAccount = (data: any) => {
    const accountData = {
      ...data,
      parent_account_id: data.parent_account_id ? parseInt(data.parent_account_id) : undefined,
      is_header: data.is_header === 'true',
      allow_posting: data.allow_posting === 'true',
      budget_enabled: data.budget_enabled === 'true',
      is_active: data.is_active === 'true',
      analysis_required: data.analysis_required === 'true',
    }
    createMutation.mutate(accountData)
  }

  const handleEditAccount = (data: any) => {
    if (selectedAccount?.id) {
      const accountData = {
        ...data,
        parent_account_id: data.parent_account_id ? parseInt(data.parent_account_id) : undefined,
        is_header: data.is_header === 'true',
        allow_posting: data.allow_posting === 'true',
        budget_enabled: data.budget_enabled === 'true',
        is_active: data.is_active === 'true',
        analysis_required: data.analysis_required === 'true',
      }
      updateMutation.mutate({ id: selectedAccount.id, data: accountData })
    }
  }

  const handleDeleteAccount = (account: ChartOfAccount) => {
    setAccountToDelete(account)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (accountToDelete?.id) {
      deleteMutation.mutate(accountToDelete.id)
      setShowDeleteDialog(false)
      setAccountToDelete(null)
    }
  }

  const handleToggleActive = (account: ChartOfAccount) => {
    if (account.id) {
      toggleActiveMutation.mutate({ id: account.id, isActive: !account.is_active })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading chart of accounts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load chart of accounts</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['chartOfAccounts'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Chart of Accounts"
        description="Manage your chart of accounts structure and hierarchy"
        breadcrumbs={[
          { label: 'General Ledger', href: '/general' },
          { label: 'Chart of Accounts' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await chartOfAccountsApi.getBalances()
                  toast.success('Account balances report generated')
                } catch (error) {
                  toast.error('Failed to generate balances report')
                }
              }}
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Account Balances
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await chartOfAccountsApi.getBudgetComparison()
                  toast.success('Budget comparison generated')
                } catch (error) {
                  toast.error('Failed to generate budget comparison')
                }
              }}
            >
              Budget vs Actual
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const blob = await chartOfAccountsApi.export('excel')
                  toast.success('Chart of accounts exported')
                } catch (error) {
                  toast.error('Failed to export chart of accounts')
                }
              }}
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
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
                      const response = await fetch('/api/v1/general/accounts/import', {
                        method: 'POST',
                        headers: {
                          'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: formData
                      })
                      if (response.ok) {
                        const result = await response.json()
                        toast.success(`Imported ${result.imported_count} accounts successfully`)
                        window.location.reload()
                      } else {
                        toast.error('Failed to import accounts')
                      }
                    } catch (error) {
                      console.error('Error importing accounts:', error)
                      toast.error('Error importing accounts')
                    }
                  }
                }
                input.click()
              }}
            >
              <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Account
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={accounts || []}
        searchPlaceholder="Search accounts..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Account"
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Account Creation Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Use format ####.#### for account codes (e.g., 1000.0001)</li>
              <li>Header accounts cannot have transactions posted to them</li>
              <li>Select appropriate parent account for hierarchy</li>
              <li>Enable budget tracking if required for reporting</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreateAccount}
            onCancel={() => setShowCreateModal(false)}
            schema={accountSchema}
            submitLabel="Create Account"
            loading={createMutation.isPending}
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Account"
        size="lg"
      >
        {selectedAccount && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditAccount}
            onCancel={() => setShowEditModal(false)}
            schema={accountSchema}
            submitLabel="Update Account"
            loading={updateMutation.isPending}
            defaultValues={{
              account_code: selectedAccount.account_code,
              account_name: selectedAccount.account_name,
              account_type: selectedAccount.account_type,
              parent_account_id: selectedAccount.parent_account_id?.toString() || '',
              is_header: selectedAccount.is_header.toString(),
              allow_posting: selectedAccount.allow_posting.toString(),
              budget_enabled: selectedAccount.budget_enabled.toString(),
              is_active: selectedAccount.is_active.toString(),
              tax_code: selectedAccount.tax_code || '',
              analysis_required: selectedAccount.analysis_required?.toString() || 'false',
              currency_code: selectedAccount.currency_code || '',
              notes: selectedAccount.notes || '',
            }}
          />
        )}
      </Modal>

      {/* Statement Modal */}
      <Modal
        isOpen={showStatementModal}
        onClose={() => setShowStatementModal(false)}
        title={`Account Statement - ${selectedAccount?.account_code}`}
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-sm text-gray-700">Account Details</h4>
            <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Account:</span> {selectedAccount?.account_name}
              </div>
              <div>
                <span className="text-gray-500">Type:</span> {selectedAccount?.account_type}
              </div>
              <div>
                <span className="text-gray-500">Current Balance:</span>{' '}
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: selectedAccount?.currency_code || 'USD',
                }).format(selectedAccount?.current_balance || 0)}
              </div>
              <div>
                <span className="text-gray-500">YTD Movement:</span>{' '}
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: selectedAccount?.currency_code || 'USD',
                }).format(selectedAccount?.ytd_movement || 0)}
              </div>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline"
              onClick={async () => {
                if (selectedAccount?.account_code) {
                  try {
                    await chartOfAccountsApi.getStatement(selectedAccount.account_code)
                    toast.success('Statement generated')
                  } catch (error) {
                    toast.error('Failed to generate statement')
                  }
                }
              }}
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Download Statement
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                if (selectedAccount?.account_code) {
                  try {
                    await chartOfAccountsApi.getHistory(selectedAccount.account_code)
                    toast.success('Transaction history loaded')
                  } catch (error) {
                    toast.error('Failed to load transaction history')
                  }
                }
              }}
            >
              View Transactions
            </Button>
          </div>
          
          <div className="text-center py-8 text-gray-500">
            Transaction history will be displayed here
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setAccountToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Account"
        message={`Are you sure you want to delete account ${accountToDelete?.account_code} - ${accountToDelete?.account_name}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}