/**
 * Tests for DataTable component
 * Tests the business component functionality with TanStack Table
 */
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ColumnDef } from '@tanstack/react-table'
import { DataTable } from '@/components/business/data-table'

// Mock data for testing
interface TestData {
  id: number
  name: string
  email: string
  status: string
}

const mockData: TestData[] = [
  { id: 1, name: 'John Doe', email: 'john@example.com', status: 'Active' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'Inactive' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'Active' },
]

const mockColumns: ColumnDef<TestData>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'email',
    header: 'Email',
  },
  {
    accessorKey: 'status',
    header: 'Status',
  },
]

describe('DataTable Component', () => {
  it('renders table with data', () => {
    render(<DataTable columns={mockColumns} data={mockData} />)
    
    // Check headers
    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    
    // Check data rows
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument()
  })

  it('renders empty state when no data', () => {
    render(<DataTable columns={mockColumns} data={[]} />)
    
    expect(screen.getByText(/no results/i)).toBeInTheDocument()
  })

  it('handles search functionality', () => {
    render(
      <DataTable 
        columns={mockColumns} 
        data={mockData} 
        searchPlaceholder="Search users..."
      />
    )
    
    const searchInput = screen.getByPlaceholderText('Search users...')
    expect(searchInput).toBeInTheDocument()
    
    // Search for "John"
    fireEvent.change(searchInput, { target: { value: 'John' } })
    
    // Should show John Doe and Bob Johnson (both contain "John")
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument()
    expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
  })

  it('handles column sorting', () => {
    render(<DataTable columns={mockColumns} data={mockData} />)
    
    const nameHeader = screen.getByText('Name')
    
    // Click to sort ascending
    fireEvent.click(nameHeader)
    
    // Check if sorting indicator is present
    const sortButton = nameHeader.closest('button')
    expect(sortButton).toBeInTheDocument()
  })

  it('handles pagination when enabled', () => {
    const largeData = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      status: i % 2 === 0 ? 'Active' : 'Inactive',
    }))
    
    render(
      <DataTable 
        columns={mockColumns} 
        data={largeData}
        enablePagination={true}
      />
    )
    
    // Should show pagination controls
    expect(screen.getByText(/previous/i)).toBeInTheDocument()
    expect(screen.getByText(/next/i)).toBeInTheDocument()
    expect(screen.getByText(/page/i)).toBeInTheDocument()
  })

  it('supports custom cell rendering', () => {
    const customColumns: ColumnDef<TestData>[] = [
      {
        accessorKey: 'name',
        header: 'Name',
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => {
          const status = row.getValue('status') as string
          return (
            <span 
              className={status === 'Active' ? 'text-green-600' : 'text-red-600'}
              data-testid="status-cell"
            >
              {status}
            </span>
          )
        },
      },
    ]
    
    render(<DataTable columns={customColumns} data={mockData} />)
    
    const statusCells = screen.getAllByTestId('status-cell')
    expect(statusCells).toHaveLength(3)
    expect(statusCells[0]).toHaveClass('text-green-600') // Active
    expect(statusCells[1]).toHaveClass('text-red-600')   // Inactive
  })

  it('handles row selection when enabled', () => {
    render(
      <DataTable 
        columns={mockColumns} 
        data={mockData}
        enableRowSelection={true}
      />
    )
    
    // Should have select all checkbox in header
    const selectAllCheckbox = screen.getAllByRole('checkbox')[0]
    expect(selectAllCheckbox).toBeInTheDocument()
    
    // Should have individual row checkboxes
    const rowCheckboxes = screen.getAllByRole('checkbox')
    expect(rowCheckboxes).toHaveLength(4) // 1 select all + 3 row checkboxes
  })

  it('shows loading state', () => {
    render(
      <DataTable 
        columns={mockColumns} 
        data={[]}
        loading={true}
      />
    )
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('handles column visibility', () => {
    render(<DataTable columns={mockColumns} data={mockData} />)
    
    // Should have column visibility toggle
    const viewButton = screen.getByText(/view/i)
    expect(viewButton).toBeInTheDocument()
    
    fireEvent.click(viewButton)
    
    // Should show column toggles
    expect(screen.getByText('Toggle columns')).toBeInTheDocument()
  })

  it('supports custom table className', () => {
    const { container } = render(
      <DataTable 
        columns={mockColumns} 
        data={mockData}
        className="custom-table-class"
      />
    )
    
    const table = container.querySelector('table')
    expect(table).toHaveClass('custom-table-class')
  })

  it('handles empty search results', () => {
    render(
      <DataTable 
        columns={mockColumns} 
        data={mockData}
        searchPlaceholder="Search..."
      />
    )
    
    const searchInput = screen.getByPlaceholderText('Search...')
    
    // Search for something that doesn't exist
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } })
    
    expect(screen.getByText(/no results/i)).toBeInTheDocument()
  })

  it('maintains search state', () => {
    render(
      <DataTable 
        columns={mockColumns} 
        data={mockData}
        searchPlaceholder="Search..."
      />
    )
    
    const searchInput = screen.getByPlaceholderText('Search...') as HTMLInputElement
    
    fireEvent.change(searchInput, { target: { value: 'John' } })
    
    expect(searchInput.value).toBe('John')
  })

  it('handles keyboard navigation', () => {
    render(<DataTable columns={mockColumns} data={mockData} />)
    
    const table = screen.getByRole('table')
    expect(table).toBeInTheDocument()
    
    // Table should be focusable for keyboard navigation
    expect(table).toHaveAttribute('tabIndex')
  })

  it('supports action buttons per row', () => {
    const columnsWithActions: ColumnDef<TestData>[] = [
      ...mockColumns,
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <button 
            data-testid={`edit-${row.original.id}`}
            onClick={() => {}}
          >
            Edit
          </button>
        ),
      },
    ]
    
    render(<DataTable columns={columnsWithActions} data={mockData} />)
    
    expect(screen.getByTestId('edit-1')).toBeInTheDocument()
    expect(screen.getByTestId('edit-2')).toBeInTheDocument()
    expect(screen.getByTestId('edit-3')).toBeInTheDocument()
  })
})