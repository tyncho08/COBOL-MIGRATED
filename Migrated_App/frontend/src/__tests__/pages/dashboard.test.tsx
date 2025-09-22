/**
 * Tests for Dashboard page
 * Tests the main dashboard functionality and components
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '@/app/(dashboard)/dashboard/page'

// Mock the chart components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="chart-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
}))

// Mock the API calls
const mockDashboardData = {
  totalSales: 125000,
  totalPurchases: 85000,
  totalCustomers: 450,
  totalSuppliers: 120,
  pendingOrders: 15,
  lowStockItems: 8,
  overdueInvoices: 3,
  cashBalance: 95000,
}

const mockRecentActivity = [
  {
    id: 1,
    type: 'sale',
    description: 'Sales Order SO001234 created',
    amount: 1500,
    timestamp: '2024-01-15T10:30:00Z',
  },
  {
    id: 2,
    type: 'purchase',
    description: 'Purchase Order PO001234 approved',
    amount: 2500,
    timestamp: '2024-01-15T09:15:00Z',
  },
]

const mockSalesData = [
  { month: 'Jan', sales: 120000, purchases: 80000 },
  { month: 'Feb', sales: 135000, purchases: 85000 },
  { month: 'Mar', sales: 125000, purchases: 90000 },
]

// Mock fetch functions
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
    },
  })

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('Dashboard Page', () => {
  beforeEach(() => {
    ;(fetch as jest.MockedFunction<typeof fetch>).mockClear()
  })

  it('renders dashboard with loading state initially', () => {
    // Mock pending promises
    ;(fetch as jest.MockedFunction<typeof fetch>).mockReturnValue(
      new Promise(() => {}) // Never resolves
    )

    renderWithQueryClient(<DashboardPage />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/overview of your accounting system/i)).toBeInTheDocument()
  })

  it('renders dashboard statistics when data loads', async () => {
    // Mock successful API responses
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('$125,000')).toBeInTheDocument() // Total Sales
    })

    expect(screen.getByText('$85,000')).toBeInTheDocument() // Total Purchases
    expect(screen.getByText('450')).toBeInTheDocument() // Total Customers
    expect(screen.getByText('120')).toBeInTheDocument() // Total Suppliers
  })

  it('displays stat cards with correct icons and values', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Total Sales')).toBeInTheDocument()
    })

    expect(screen.getByText('Total Purchases')).toBeInTheDocument()
    expect(screen.getByText('Total Customers')).toBeInTheDocument()
    expect(screen.getByText('Total Suppliers')).toBeInTheDocument()
  })

  it('renders charts section', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Sales vs Purchases')).toBeInTheDocument()
    })

    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('displays recent activity section', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    })

    expect(screen.getByText('Sales Order SO001234 created')).toBeInTheDocument()
    expect(screen.getByText('Purchase Order PO001234 approved')).toBeInTheDocument()
  })

  it('shows alerts for important items', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText(/15.*pending orders/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/8.*low stock items/i)).toBeInTheDocument()
    expect(screen.getByText(/3.*overdue invoices/i)).toBeInTheDocument()
  })

  it('handles API error states gracefully', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>).mockRejectedValue(
      new Error('API Error')
    )

    renderWithQueryClient(<DashboardPage />)

    // Dashboard should still render the basic structure
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('formats currency values correctly', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      // Check that currency is formatted with $ symbol and commas
      expect(screen.getByText('$125,000')).toBeInTheDocument()
    })

    expect(screen.getByText('$85,000')).toBeInTheDocument()
    expect(screen.getByText('$95,000')).toBeInTheDocument() // Cash balance
  })

  it('displays timestamps in recent activity', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      // Should display formatted timestamps
      expect(screen.getByText(/10:30/)).toBeInTheDocument()
    })

    expect(screen.getByText(/09:15/)).toBeInTheDocument()
  })

  it('has proper accessibility attributes', async () => {
    ;(fetch as jest.MockedFunction<typeof fetch>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    // Check for proper heading structure
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
  })

  it('refreshes data when needed', async () => {
    const mockFetch = fetch as jest.MockedFunction<typeof fetch>
    
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboardData,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecentActivity,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSalesData,
      } as Response)

    renderWithQueryClient(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('$125,000')).toBeInTheDocument()
    })

    // Verify that API calls were made
    expect(mockFetch).toHaveBeenCalled()
  })
})