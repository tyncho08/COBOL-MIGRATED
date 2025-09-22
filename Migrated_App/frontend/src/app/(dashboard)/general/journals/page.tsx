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
  DocumentCheckIcon,
  ArrowPathIcon,
  CalculatorIcon,
  PrinterIcon,
  TrashIcon,
  DocumentArrowDownIcon,
  XCircleIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline'
import { z } from 'zod'
import { JournalEntry, JournalLine, journalEntriesApi } from '@/lib/api/journal-entries'
import { chartOfAccountsApi } from '@/lib/api/chart-of-accounts'
import toast from 'react-hot-toast'
import { useAuth } from '@/lib/auth/context'

// Schema
const journalEntrySchema = z.object({
  journal_date: z.string().min(1, 'Journal date is required'),
  journal_type: z.string().min(1, 'Journal type is required'),
  reference: z.string().optional(),
  description: z.string().min(1, 'Description is required'),
  notes: z.string().optional(),
})

const journalLineSchema = z.object({
  account_code: z.string().min(1, 'Account code is required'),
  description: z.string().min(1, 'Line description is required'),
  debit_amount: z.string().optional(),
  credit_amount: z.string().optional(),
  analysis_code: z.string().optional(),
  reference: z.string().optional(),
})

const reversalSchema = z.object({
  reversal_date: z.string().min(1, 'Reversal date is required'),
  reversal_reason: z.string().min(1, 'Reversal reason is required'),
  reversal_reference: z.string().optional(),
})

const getJournalTypeBadge = (type: string) => {
  switch (type) {
    case 'GENERAL':
      return <Badge variant="info">General</Badge>
    case 'ACCRUAL':
      return <Badge variant="warning">Accrual</Badge>
    case 'CORRECTION':
      return <Badge variant="danger">Correction</Badge>
    case 'RECLASSIFICATION':
      return <Badge variant="default">Reclassification</Badge>
    case 'DEPRECIATION':
      return <Badge variant="default">Depreciation</Badge>
    case 'CONSOLIDATION':
      return <Badge variant="info">Consolidation</Badge>
    case 'YEAR_END':
      return <Badge variant="success">Year End</Badge>
    default:
      return <Badge variant="default">{type}</Badge>
  }
}

const getPostingStatusBadge = (status: string, isReversed?: boolean) => {
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
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showLinesModal, setShowLinesModal] = useState(false)
  const [showAddLineModal, setShowAddLineModal] = useState(false)
  const [showReversalModal, setShowReversalModal] = useState(false)
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null)
  const [entryToDelete, setEntryToDelete] = useState<JournalEntry | null>(null)
  const [entryToReverse, setEntryToReverse] = useState<JournalEntry | null>(null)

  const queryClient = useQueryClient()
  const { canEdit, canDelete } = useAuth()

  // Query for journal entries
  const { data: journalEntries, isLoading, error } = useQuery({
    queryKey: ['journalEntries'],
    queryFn: () => journalEntriesApi.getAll(),
  })

  // Query for accounts
  const { data: accounts } = useQuery({
    queryKey: ['chartOfAccounts'],
    queryFn: () => chartOfAccountsApi.getAll(),
  })

  // Query for journal lines when viewing
  const { data: journalLines } = useQuery({
    queryKey: ['journalLines', selectedEntry?.id],
    queryFn: () => selectedEntry?.id ? journalEntriesApi.getLines(selectedEntry.id) : null,
    enabled: !!selectedEntry?.id && showLinesModal,
  })

  // Mutation for creating journal entry
  const createMutation = useMutation({
    mutationFn: journalEntriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      toast.success('Journal entry created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create journal entry')
    },
  })

  // Mutation for updating journal entry
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<JournalEntry> }) =>
      journalEntriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      toast.success('Journal entry updated successfully')
      setShowEditModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update journal entry')
    },
  })

  // Mutation for deleting journal entry
  const deleteMutation = useMutation({
    mutationFn: journalEntriesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      toast.success('Journal entry deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete journal entry')
    },
  })

  // Mutation for posting journal entry
  const postMutation = useMutation({
    mutationFn: journalEntriesApi.post,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      toast.success('Journal entry posted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to post journal entry')
    },
  })

  // Mutation for reversing journal entry
  const reverseMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      journalEntriesApi.reverse(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      toast.success('Journal entry reversed successfully')
      setShowReversalModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reverse journal entry')
    },
  })

  // Mutation for adding journal line
  const addLineMutation = useMutation({
    mutationFn: ({ journalId, line }: { journalId: number; line: Omit<JournalLine, 'id'> }) =>
      journalEntriesApi.addLine(journalId, line),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
      queryClient.invalidateQueries({ queryKey: ['journalLines'] })
      toast.success('Line added successfully')
      setShowAddLineModal(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add line')
    },
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
      cell: ({ row }) => row.getValue('reference') || '-',
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
        const amount = parseFloat(row.getValue('total_debits') || '0')
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
        const amount = parseFloat(row.getValue('total_credits') || '0')
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
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const entry = row.original
        const isDraft = entry.posting_status === 'DRAFT'
        const isPending = entry.posting_status === 'PENDING'
        const isPosted = entry.posting_status === 'POSTED'
        
        return (
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedEntry(entry)
                setShowEditModal(true)
              }}
              disabled={!isDraft}
              title="Edit"
            >
              <PencilIcon className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSelectedEntry(entry)
                setShowLinesModal(true)
              }}
              title="View Lines"
            >
              <ClipboardDocumentListIcon className="h-4 w-4" />
            </Button>
            {isPending && entry.is_balanced && canEdit('general') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handlePost(entry)}
                title="Post Entry"
                className="text-green-600 hover:text-green-700"
              >
                <DocumentCheckIcon className="h-4 w-4" />
              </Button>
            )}
            {isPosted && !entry.is_reversed && canEdit('general') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleReverse(entry)}
                title="Reverse Entry"
                className="text-orange-600 hover:text-orange-700"
              >
                <ArrowPathIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={async () => {
                try {
                  await journalEntriesApi.print(entry.id!)
                  toast.success('Journal entry printed')
                } catch (error) {
                  toast.error('Failed to print journal entry')
                }
              }}
              title="Print"
            >
              <PrinterIcon className="h-4 w-4" />
            </Button>
            {isDraft && canDelete('general') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDeleteEntry(entry)}
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
      name: 'journal_date',
      label: 'Journal Date',
      type: 'date',
      required: true,
    },
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
        { value: 'CONSOLIDATION', label: 'Consolidation' },
        { value: 'YEAR_END', label: 'Year End' },
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
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
    },
  ]

  const lineFormFields: FormField[] = [
    {
      name: 'account_code',
      label: 'Account',
      type: 'select',
      required: true,
      options: Array.isArray(accounts)
        ? accounts.filter(a => a.allow_posting).map(a => ({ 
            value: a.account_code, 
            label: `${a.account_code} - ${a.account_name}` 
          }))
        : [],
    },
    {
      name: 'description',
      label: 'Description',
      type: 'text',
      required: true,
    },
    {
      name: 'debit_amount',
      label: 'Debit Amount',
      type: 'number',
    },
    {
      name: 'credit_amount',
      label: 'Credit Amount',
      type: 'number',
    },
    {
      name: 'analysis_code',
      label: 'Analysis Code',
      type: 'text',
    },
    {
      name: 'reference',
      label: 'Reference',
      type: 'text',
    },
  ]

  const reversalFormFields: FormField[] = [
    {
      name: 'reversal_date',
      label: 'Reversal Date',
      type: 'date',
      required: true,
    },
    {
      name: 'reversal_reason',
      label: 'Reversal Reason',
      type: 'select',
      required: true,
      options: [
        { value: 'ERROR', label: 'Posting Error' },
        { value: 'INCORRECT_AMOUNT', label: 'Incorrect Amount' },
        { value: 'WRONG_ACCOUNT', label: 'Wrong Account' },
        { value: 'DUPLICATE', label: 'Duplicate Entry' },
        { value: 'OTHER', label: 'Other' },
      ],
    },
    {
      name: 'reversal_reference',
      label: 'Reversal Reference',
      type: 'text',
    },
  ]

  const handleCreateEntry = (data: any) => {
    const entryData = {
      ...data,
      posting_status: 'DRAFT' as const,
      journal_lines: [],
    }
    createMutation.mutate(entryData)
  }

  const handleEditEntry = (data: any) => {
    if (selectedEntry?.id) {
      updateMutation.mutate({ id: selectedEntry.id, data })
    }
  }

  const handleDeleteEntry = (entry: JournalEntry) => {
    setEntryToDelete(entry)
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    if (entryToDelete?.id) {
      deleteMutation.mutate(entryToDelete.id)
      setShowDeleteDialog(false)
      setEntryToDelete(null)
    }
  }

  const handlePost = (entry: JournalEntry) => {
    if (entry.id) {
      postMutation.mutate(entry.id)
    }
  }

  const handleReverse = (entry: JournalEntry) => {
    setEntryToReverse(entry)
    setShowReversalModal(true)
  }

  const handleReversalSubmit = (data: any) => {
    if (entryToReverse?.id) {
      reverseMutation.mutate({ id: entryToReverse.id, data })
    }
  }

  const handleAddLine = (data: any) => {
    if (selectedEntry?.id) {
      const lineData = {
        line_number: (journalLines?.length || 0) + 1,
        account_code: data.account_code,
        account_name: accounts?.find(a => a.account_code === data.account_code)?.account_name || '',
        description: data.description,
        debit_amount: parseFloat(data.debit_amount || '0'),
        credit_amount: parseFloat(data.credit_amount || '0'),
        analysis_code: data.analysis_code,
        reference: data.reference,
      }
      addLineMutation.mutate({ journalId: selectedEntry.id, line: lineData })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading journal entries...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load journal entries</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['journalEntries'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
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
              onClick={async () => {
                try {
                  await journalEntriesApi.getTrialBalance()
                  toast.success('Trial balance generated')
                } catch (error) {
                  toast.error('Failed to generate trial balance')
                }
              }}
            >
              <CalculatorIcon className="h-4 w-4 mr-2" />
              Trial Balance
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                toast('Batch posting coming soon')
              }}
            >
              Batch Post
            </Button>
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  const blob = await journalEntriesApi.export({ format: 'excel' })
                  toast.success('Journal entries exported')
                } catch (error) {
                  toast.error('Failed to export journal entries')
                }
              }}
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
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
            loading={createMutation.isPending}
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
            loading={updateMutation.isPending}
            defaultValues={{
              journal_date: selectedEntry.journal_date,
              journal_type: selectedEntry.journal_type,
              reference: selectedEntry.reference,
              description: selectedEntry.description,
              notes: selectedEntry.notes,
            }}
          />
        )}
      </Modal>

      {/* Journal Lines Modal */}
      <Modal
        isOpen={showLinesModal}
        onClose={() => setShowLinesModal(false)}
        title={`Journal Lines - ${selectedEntry?.journal_number}`}
        size="xl"
      >
        <div className="space-y-4">
          {selectedEntry?.posting_status === 'DRAFT' && canEdit('general') && (
            <div className="flex justify-end">
              <Button onClick={() => setShowAddLineModal(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Line
              </Button>
            </div>
          )}
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Line
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Debit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Analysis
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reference
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {journalLines?.map((line) => (
                  <tr key={line.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {line.line_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{line.account_code}</div>
                        {line.account_name && (
                          <div className="text-sm text-gray-500">{line.account_name}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {line.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {line.debit_amount > 0 ? new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      }).format(line.debit_amount) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {line.credit_amount > 0 ? new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      }).format(line.credit_amount) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.analysis_code || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {line.reference || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50">
                  <td colSpan={3} className="px-6 py-3 text-right font-medium">
                    Totals:
                  </td>
                  <td className="px-6 py-3 font-medium">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedEntry?.total_debits || 0)}
                  </td>
                  <td className="px-6 py-3 font-medium">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedEntry?.total_credits || 0)}
                  </td>
                  <td colSpan={2} className="px-6 py-3">
                    {selectedEntry?.is_balanced ? (
                      <Badge variant="success">Balanced</Badge>
                    ) : (
                      <Badge variant="danger">Not Balanced</Badge>
                    )}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
          
          {(!journalLines || journalLines.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              No lines added yet
            </div>
          )}
        </div>
      </Modal>

      {/* Add Line Modal */}
      <Modal
        isOpen={showAddLineModal}
        onClose={() => setShowAddLineModal(false)}
        title="Add Journal Line"
        size="lg"
      >
        <FormBuilder
          fields={lineFormFields}
          onSubmit={handleAddLine}
          onCancel={() => setShowAddLineModal(false)}
          schema={journalLineSchema}
          submitLabel="Add Line"
          loading={addLineMutation.isPending}
        />
      </Modal>

      {/* Reversal Modal */}
      <Modal
        isOpen={showReversalModal}
        onClose={() => setShowReversalModal(false)}
        title={`Reverse Journal Entry - ${entryToReverse?.journal_number}`}
        size="lg"
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">Reversal Warning</h3>
            <p className="mt-2 text-sm text-yellow-700">
              This action will create a new journal entry that reverses all lines of the original entry.
              The original entry will be marked as reversed and cannot be modified.
            </p>
          </div>
          
          <FormBuilder
            fields={reversalFormFields}
            onSubmit={handleReversalSubmit}
            onCancel={() => setShowReversalModal(false)}
            schema={reversalSchema}
            submitLabel="Reverse Entry"
            loading={reverseMutation.isPending}
          />
        </div>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setEntryToDelete(null)
        }}
        onConfirm={confirmDelete}
        title="Delete Journal Entry"
        message={`Are you sure you want to delete journal entry ${entryToDelete?.journal_number}? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
      />
    </div>
  )
}