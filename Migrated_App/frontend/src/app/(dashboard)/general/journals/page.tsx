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
  DocumentCheckIcon,
  ArrowPathIcon,
  CalculatorIcon,
  PrinterIcon 
} from '@heroicons/react/24/outline'
import { z } from 'zod'

// Types
interface JournalEntry {
  id: number
  journal_number: string
  journal_date: string
  journal_type: string
  reference?: string
  description: string
  total_debits: number
  total_credits: number
  is_balanced: boolean
  posting_status: string
  period_number: number
  year_number: number
  posted_by?: string
  posted_date?: string
  reversed_by?: string
  reversed_date?: string
  is_reversed: boolean
  source_module?: string
  batch_number?: string
  created_by: string
  created_date: string
}

// Schema
const journalEntrySchema = z.object({
  journal_type: z.string().min(1, 'Journal type is required'),
  reference: z.string().optional(),
  description: z.string().min(1, 'Description is required'),
  journal_lines: z.array(z.object({
    account_code: z.string().min(1, 'Account code is required'),
    description: z.string().min(1, 'Line description is required'),
    debit_amount: z.string().optional(),
    credit_amount: z.string().optional(),
    analysis_code: z.string().optional(),
  })).min(2, 'At least two journal lines are required'),
})

// Mock data
const mockJournalEntries: JournalEntry[] = [
  {
    id: 1,
    journal_number: 'JE001234',
    journal_date: '2024-01-15',
    journal_type: 'GENERAL',
    reference: 'ADJ-2024-001',
    description: 'Monthly depreciation adjustment',
    total_debits: 1500.00,
    total_credits: 1500.00,
    is_balanced: true,
    posting_status: 'POSTED',
    period_number: 1,
    year_number: 2024,
    posted_by: 'Manager',
    posted_date: '2024-01-15T10:30:00Z',
    is_reversed: false,
    source_module: 'GL',
    created_by: 'John Smith',
    created_date: '2024-01-15T09:00:00Z',
  },
  {
    id: 2,
    journal_number: 'JE001235',
    journal_date: '2024-01-16',
    journal_type: 'ACCRUAL',
    reference: 'ACC-2024-001',
    description: 'Accrued expenses for January',
    total_debits: 2500.00,
    total_credits: 2500.00,
    is_balanced: true,
    posting_status: 'PENDING',
    period_number: 1,
    year_number: 2024,
    is_reversed: false,
    source_module: 'GL',
    created_by: 'Jane Doe',
    created_date: '2024-01-16T14:00:00Z',
  },
  {
    id: 3,
    journal_number: 'JE001236',
    journal_date: '2024-01-17',
    journal_type: 'CORRECTION',
    reference: 'COR-2024-001',
    description: 'Correction of posting error',
    total_debits: 750.00,
    total_credits: 750.00,
    is_balanced: true,
    posting_status: 'DRAFT',
    period_number: 1,
    year_number: 2024,
    is_reversed: false,
    source_module: 'GL',
    created_by: 'Bob Johnson',
    created_date: '2024-01-17T11:30:00Z',
  },
  {
    id: 4,
    journal_number: 'JE001237',
    journal_date: '2024-01-10',
    journal_type: 'GENERAL',
    reference: 'REV-2024-001',
    description: 'Reversed: Incorrect allocation',
    total_debits: 1000.00,
    total_credits: 1000.00,
    is_balanced: true,
    posting_status: 'POSTED',
    period_number: 1,
    year_number: 2024,
    posted_by: 'Manager',
    posted_date: '2024-01-10T16:00:00Z',
    reversed_by: 'Manager',
    reversed_date: '2024-01-18T09:00:00Z',
    is_reversed: true,
    source_module: 'GL',
    created_by: 'Alice Wilson',
    created_date: '2024-01-10T15:30:00Z',
  },
]

const getJournalTypeBadge = (type: string) => {
  switch (type) {
    case 'GENERAL':
      return <Badge variant="info">General</Badge>
    case 'ACCRUAL':
      return <Badge variant="warning">Accrual</Badge>
    case 'CORRECTION':
      return <Badge variant="danger">Correction</Badge>
    case 'RECLASSIFICATION':
      return <Badge variant="secondary">Reclassification</Badge>
    case 'DEPRECIATION':
      return <Badge variant="default">Depreciation</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getPostingStatusBadge = (status: string, isReversed: boolean) => {
  if (isReversed) {
    return <Badge variant="danger">Reversed</Badge>
  }
  
  switch (status) {
    case 'DRAFT':
      return <Badge variant="default">Draft</Badge>
    case 'PENDING':
      return <Badge variant="warning">Pending</Badge>
    case 'POSTED':
      return <Badge variant="success">Posted</Badge>
    case 'REJECTED':
      return <Badge variant="danger">Rejected</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function JournalEntriesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null)

  const { data: journalEntries, isLoading } = useQuery({
    queryKey: ['journal-entries'],
    queryFn: () => Promise.resolve(mockJournalEntries),
  })

  const columns: ColumnDef<JournalEntry>[] = [
    {
      accessorKey: 'journal_number',
      header: 'Journal Number',
    },
    {
      accessorKey: 'journal_date',
      header: 'Journal Date',
      cell: ({ row }) => {
        const date = row.getValue('journal_date') as string
        return new Date(date).toLocaleDateString()
      },
    },
    {
      accessorKey: 'journal_type',
      header: 'Type',
      cell: ({ row }) => {
        return getJournalTypeBadge(row.getValue('journal_type'))
      },
    },
    {
      accessorKey: 'reference',
      header: 'Reference',
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
        const entry = row.original
        return entry.is_balanced ? (
          <Badge variant="success">Yes</Badge>
        ) : (
          <Badge variant="danger">No</Badge>
        )
      },
    },
    {
      accessorKey: 'posting_status',
      header: 'Status',
      cell: ({ row }) => {
        const entry = row.original
        return getPostingStatusBadge(row.getValue('posting_status'), entry.is_reversed)
      },
    },
    {
      accessorKey: 'period_number',
      header: 'Period',
      cell: ({ row }) => {
        const period = row.getValue('period_number') as number
        const year = row.original.year_number
        return `${period}/${year}`
      },
    },
    {
      accessorKey: 'created_by',
      header: 'Created By',
    },
    {
      accessorKey: 'posted_by',
      header: 'Posted By',
    },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => {
        const entry = row.original
        return (
          <div className="flex space-x-1">
            {entry.source_module && (
              <Badge variant="outline" className="text-xs">{entry.source_module}</Badge>
            )}
            {entry.batch_number && (
              <Badge variant="info" className="text-xs">BATCH</Badge>
            )}
            {entry.is_reversed && (
              <Badge variant="danger" className="text-xs">REV</Badge>
            )}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const entry = row.original
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedEntry(entry)
                setShowEditModal(true)
              }}
              disabled={entry.posting_status === 'POSTED' && !entry.is_reversed}
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle view entry details
              }}
            >
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                // Handle print journal entry
              }}
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {entry.posting_status === 'PENDING' && entry.is_balanced && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle post journal entry
                }}
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {entry.posting_status === 'POSTED' && !entry.is_reversed && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // Handle reverse journal entry
                }}
              >
                <ArrowPathIcon className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const formFields: FormField[] = [
    {
      name: 'journal_type',
      label: 'Journal Type',
      type: 'select',
      required: true,
      options: [
        { value: 'GENERAL', label: 'General Journal' },
        { value: 'ACCRUAL', label: 'Accrual Entry' },
        { value: 'CORRECTION', label: 'Correction Entry' },
        { value: 'RECLASSIFICATION', label: 'Reclassification' },
        { value: 'DEPRECIATION', label: 'Depreciation' },
      ],
    },
    {
      name: 'reference',
      label: 'Reference',
      type: 'text',
    },
    {
      name: 'description',
      label: 'Description',
      type: 'text',
      required: true,
    },
  ]

  const handleCreateEntry = (data: any) => {
    console.log('Creating journal entry:', data)
    setShowCreateModal(false)
  }

  const handleEditEntry = (data: any) => {
    console.log('Editing journal entry:', data)
    setShowEditModal(false)
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <PageHeader
        title="Journal Entries"
        description="Manage general ledger journal entries and postings"
        breadcrumbs={[
          { label: 'General Ledger', href: '/general' },
          { label: 'Journal Entries' },
        ]}
        actions={
          <div className="flex space-x-2">
            <Button 
              variant="outline"
              onClick={() => {
                // Handle trial balance
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Trial Balance
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                // Handle batch posting
              }}
            >
              Batch Post
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Journal Entry
            </Button>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={journalEntries || []}
        searchPlaceholder="Search journal entries..."
      />

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Journal Entry"
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">Journal Entry Guidelines</h3>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
              <li>Ensure total debits equal total credits</li>
              <li>Provide clear descriptions for all lines</li>
              <li>Verify account codes are valid</li>
              <li>Include appropriate analysis codes where required</li>
            </ul>
          </div>
          
          <FormBuilder
            fields={formFields}
            onSubmit={handleCreateEntry}
            onCancel={() => setShowCreateModal(false)}
            schema={journalEntrySchema}
            submitLabel="Create Journal Entry"
          />
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Journal Entry"
        size="xl"
      >
        {selectedEntry && (
          <FormBuilder
            fields={formFields}
            onSubmit={handleEditEntry}
            onCancel={() => setShowEditModal(false)}
            schema={journalEntrySchema}
            submitLabel="Update Journal Entry"
            defaultValues={{
              journal_type: selectedEntry.journal_type,
              reference: selectedEntry.reference,
              description: selectedEntry.description,
            }}
          />
        )}
      </Modal>
    </div>
  )
}