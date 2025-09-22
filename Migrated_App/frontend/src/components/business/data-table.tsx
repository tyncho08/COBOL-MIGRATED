'use client'

import { useState, useRef, useEffect } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
  ColumnFiltersState,
  ColumnDef,
} from '@tanstack/react-table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Select } from '@/components/ui/select'

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchPlaceholder?: string
  enableSearch?: boolean
  enablePagination?: boolean
  pageSize?: number
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchPlaceholder = 'Search...',
  enableSearch = true,
  enablePagination = true,
  pageSize = 10
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [showLeftShadow, setShowLeftShadow] = useState(false)
  const [showRightShadow, setShowRightShadow] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const checkScroll = () => {
      const element = scrollRef.current
      if (element) {
        const { scrollLeft, scrollWidth, clientWidth } = element
        setShowLeftShadow(scrollLeft > 0)
        setShowRightShadow(scrollLeft + clientWidth < scrollWidth - 1)
      }
    }
    
    // Check on mount
    checkScroll()
    
    // Check on window resize
    window.addEventListener('resize', checkScroll)
    return () => window.removeEventListener('resize', checkScroll)
  }, [data]) // Re-check when data changes

  const handleScroll = () => {
    const element = scrollRef.current
    if (element) {
      const { scrollLeft, scrollWidth, clientWidth } = element
      setShowLeftShadow(scrollLeft > 0)
      setShowRightShadow(scrollLeft + clientWidth < scrollWidth - 1)
    }
  }

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  })

  return (
    <div className="space-y-4">
      {enableSearch && (
        <div className="flex items-center py-4">
          <Input
            placeholder={searchPlaceholder}
            value={globalFilter ?? ''}
            onChange={(event) => setGlobalFilter(String(event.target.value))}
            className="max-w-sm"
          />
        </div>
      )}
      
      <div className="relative rounded-md border overflow-hidden shadow ring-1 ring-black ring-opacity-5">
        {/* Subtle gradient shadows for scroll indicators */}
        {showLeftShadow && (
          <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-white/90 via-white/50 to-transparent pointer-events-none z-10" />
        )}
        {showRightShadow && (
          <div className="absolute right-0 top-0 bottom-0 w-4 bg-gradient-to-l from-white/90 via-white/50 to-transparent pointer-events-none z-10" />
        )}
        
        <div 
          className="overflow-x-auto table-scroll-container"
          ref={scrollRef}
          onScroll={handleScroll}
        >
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const isActionsColumn = header.column.id === 'actions'
                    return (
                      <TableHead
                        key={header.id}
                        sortable={header.column.getCanSort()}
                        sorted={
                          header.column.getIsSorted() === 'asc' ? 'asc' :
                          header.column.getIsSorted() === 'desc' ? 'desc' : false
                        }
                        onClick={header.column.getToggleSortingHandler()}
                        className={`whitespace-nowrap sticky top-0 bg-gray-50 ${isActionsColumn ? 'sticky-column' : ''}`}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    )
                  })}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    selected={row.getIsSelected()}
                  >
                    {row.getVisibleCells().map((cell) => {
                      // Allow wrapping for specific columns like description
                      const isWrappable = cell.column.id === 'description' || 
                                         cell.column.id === 'notes' ||
                                         cell.column.id === 'address'
                      const isActionsColumn = cell.column.id === 'actions'
                      
                      return (
                        <TableCell 
                          key={cell.id} 
                          className={`
                            ${isWrappable ? '' : 'whitespace-nowrap'}
                            ${isActionsColumn ? 'sticky-column' : ''}
                          `}
                        >
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      )
                    })}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        
        {/* Subtle scroll indicators */}
        {showRightShadow && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
            <svg className="w-6 h-6 text-gray-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        )}
        {showLeftShadow && (
          <div className="absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none">
            <svg className="w-6 h-6 text-gray-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </div>
        )}
      </div>
      
      {enablePagination && (
        <div className="flex items-center justify-between space-x-2 py-4">
          <div className="flex-1 text-sm text-gray-500">
            {table.getFilteredSelectedRowModel().rows.length} of{' '}
            {table.getFilteredRowModel().rows.length} row(s) selected.
          </div>
          <div className="flex items-center space-x-6 lg:space-x-8">
            <div className="flex items-center space-x-2">
              <p className="text-sm font-medium">Rows per page</p>
              <Select
                value={`${table.getState().pagination.pageSize}`}
                onChange={(e) => {
                  table.setPageSize(Number(e.target.value))
                }}
                options={[
                  { value: '10', label: '10' },
                  { value: '20', label: '20' },
                  { value: '30', label: '30' },
                  { value: '40', label: '40' },
                  { value: '50', label: '50' },
                ]}
              />
            </div>
            <div className="flex w-[100px] items-center justify-center text-sm font-medium">
              Page {table.getState().pagination.pageIndex + 1} of{' '}
              {table.getPageCount()}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}
              >
                {'<<'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                {'<'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                {'>'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                disabled={!table.getCanNextPage()}
              >
                {'>>'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}