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
import { PlusIcon, EyeIcon, PencilIcon } from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface ChartOfAccount {
  id: number
  account_code: string
  account_name: string
  account_type: string
  is_header: boolean
  level: number
  allow_posting: boolean
  current_balance: number
  ytd_movement: number
  is_active: boolean
}

// Schema
const accountSchema = z.object({
  account_code: z.string()
    .regex(/^\d{4}\.\d{4}$/, 'Account code must be in format ####.####'),
  account_name: z.string().min(1, 'Account name is required'),
  account_type: z.string().min(1, 'Account type is required'),
  parent_account: z.string().optional(),
  is_header: z.boolean(),
  allow_posting: z.boolean(),
  budget_enabled: z.boolean(),
  notes: z.string().optional(),
})

// Mock data
const mockAccounts: ChartOfAccount[] = [
  {
    id: 1,
    account_code: '1000.0000',
    account_name: 'Current Assets',
    account_type: 'ASSET',
    is_header: true,
    level: 0,
    allow_posting: false,
    current_balance: 0,
    ytd_movement: 0,
    is_active: true,
  },
  {
    id: 2,
    account_code: '1000.0001',
    account_name: 'Cash at Bank',
    account_type: 'ASSET',
    is_header: false,
    level: 1,
    allow_posting: true,
    current_balance: 15420.50,
    ytd_movement: 2340.50,
    is_active: true,
  },
  {
    id: 3,
    account_code: '2000.0000',
    account_name: 'Current Liabilities',
    account_type: 'LIABILITY',
    is_header: true,
    level: 0,
    allow_posting: false,
    current_balance: 0,
    ytd_movement: 0,
    is_active: true,
  },
]

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
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

export default function ChartOfAccountsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<ChartOfAccount | null>(null)

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['chart-of-accounts'],
    queryFn: () => Promise.resolve(mockAccounts),
  })

  const columns: ColumnDef<ChartOfAccount>[] = [
    {
      accessorKey: 'account_code',
      header: 'Account Code',
      cell: ({ row }) => {
        const level = row.getValue('level') as number
        const code = row.getValue('account_code') as string
        return (
          <div style={{ paddingLeft: `${level * 20}px` }}>
            {code}
          </div>
        )
      },
    },
    {
      accessorKey: 'account_name',
      header: 'Account Name',
      cell: ({ row }) => {
        const isHeader = row.getValue('is_header') as boolean
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
        const type = row.getValue('account_type') as string
        return getAccountTypeBadge(type)
      },
    },
    {
      accessorKey: 'current_balance',
      header: 'Current Balance',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('current_balance'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'ytd_movement',
      header: 'YTD Movement',
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('ytd_movement'))
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(amount)
      },
    },
    {
      accessorKey: 'allow_posting',
      header: 'Posting',
      cell: ({ row }) => {
        const allowPosting = row.getValue('allow_posting') as boolean
        return (
          <Badge variant={allowPosting ? 'success' : 'default'}>
            {allowPosting ? 'Yes' : 'No'}
          </Badge>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const account = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedAccount(account)
                setShowEditModal(true)
              }}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view account details
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
      ],
    },
    {
      name: 'parent_account',
      label: 'Parent Account',
      type: 'select',
      options: [
        { value: '', label: 'None (Top Level)' },
        { value: '1000.0000', label: '1000.0000 - Current Assets' },
        { value: '2000.0000', label: '2000.0000 - Current Liabilities' },
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
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const handleCreateAccount = (data: any) => {
    console.log('Creating account:', data)
    setShowCreateModal(false)
  }

  const handleEditAccount = (data: any) => {
    console.log('Editing account:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
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
          <Button onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Account
          </Button>
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
        <FormBuilder
          fields={formFields}
          onSubmit={handleCreateAccount}
          onCancel={() => setShowCreateModal(false)}
          schema={accountSchema}
          submitLabel="Create Account"
        />
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
            defaultValues={{
              account_code: selectedAccount.account_code,
              account_name: selectedAccount.account_name,
              account_type: selectedAccount.account_type,
              is_header: selectedAccount.is_header.toString(),
              allow_posting: selectedAccount.allow_posting.toString(),
            }}
          />
        )}
      </Modal>
    </div>
  )
}