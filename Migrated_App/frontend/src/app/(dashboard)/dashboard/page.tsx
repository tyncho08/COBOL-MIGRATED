'use client'

import { useQuery } from '@tanstack/react-query'
import { StatsCard } from '@/components/business/stats-card'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { PageHeader } from '@/components/business/page-header'
import {
  ShoppingCartIcon,
  CubeIcon,
  ChartBarIcon,
  UsersIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Badge } from '@/components/ui/badge'

// Mock dashboard data
const mockDashboardData = {
  stats: {
    totalPurchaseOrders: 156,
    pendingApprovals: 12,
    stockItems: 2847,
    lowStockItems: 23,
    totalSuppliers: 89,
    activeSuppliers: 67,
    openPeriods: 1,
    journalEntries: 1234
  },
  recentActivity: [
    {
      id: 1,
      type: 'purchase_order',
      description: 'Purchase Order PO000156 created',
      timestamp: '2024-01-20T10:30:00Z',
      status: 'pending'
    },
    {
      id: 2,
      type: 'goods_receipt',
      description: 'Goods Receipt GR000089 posted',
      timestamp: '2024-01-20T09:15:00Z',
      status: 'completed'
    },
    {
      id: 3,
      type: 'journal_entry',
      description: 'Journal Entry JE001234 posted',
      timestamp: '2024-01-20T08:45:00Z',
      status: 'completed'
    },
    {
      id: 4,
      type: 'stock_take',
      description: 'Stock Take ST000012 started',
      timestamp: '2024-01-19T16:20:00Z',
      status: 'in_progress'
    }
  ],
  alerts: [
    {
      id: 1,
      type: 'warning',
      message: '23 stock items are below reorder level',
      action: 'Review Stock'
    },
    {
      id: 2,
      type: 'info',
      message: '12 purchase orders pending approval',
      action: 'Review Orders'
    },
    {
      id: 3,
      type: 'warning',
      message: 'Period 12/2023 closing due in 3 days',
      action: 'Period End'
    }
  ]
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'purchase_order':
      return <ShoppingCartIcon className="h-5 w-5" />
    case 'goods_receipt':
      return <CubeIcon className="h-5 w-5" />
    case 'journal_entry':
      return <DocumentTextIcon className="h-5 w-5" />
    case 'stock_take':
      return <ChartBarIcon className="h-5 w-5" />
    default:
      return <DocumentTextIcon className="h-5 w-5" />
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'pending':
      return <Badge variant="warning">Pending</Badge>
    case 'completed':
      return <Badge variant="success">Completed</Badge>
    case 'in_progress':
      return <Badge variant="info">In Progress</Badge>
    default:
      return <Badge variant="default">{status}</Badge>
  }
}

export default function DashboardPage() {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => Promise.resolve(mockDashboardData),
  })

  if (isLoading) {
    return <div>Loading dashboard...</div>
  }

  const stats = dashboardData?.stats || {}
  const recentActivity = dashboardData?.recentActivity || []
  const alerts = dashboardData?.alerts || []

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your accounting system"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatsCard
          title="Purchase Orders"
          value={stats.totalPurchaseOrders}
          icon={<ShoppingCartIcon className="h-6 w-6" />}
          change={{
            value: 12,
            type: 'increase',
            period: 'last month'
          }}
          trend="up"
        />
        
        <StatsCard
          title="Stock Items"
          value={stats.stockItems}
          icon={<CubeIcon className="h-6 w-6" />}
          trend="neutral"
        />
        
        <StatsCard
          title="Suppliers"
          value={`${stats.activeSuppliers}/${stats.totalSuppliers}`}
          icon={<UsersIcon className="h-6 w-6" />}
          trend="neutral"
        />
        
        <StatsCard
          title="Journal Entries"
          value={stats.journalEntries}
          icon={<DocumentTextIcon className="h-6 w-6" />}
          change={{
            value: 8,
            type: 'increase',
            period: 'this week'
          }}
          trend="up"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center space-x-4">
                  <div className="flex-shrink-0 text-gray-400">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">
                      {activity.description}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    {getStatusBadge(activity.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Alerts & Notifications */}
        <Card>
          <CardHeader>
            <CardTitle>Alerts & Notifications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{alert.message}</p>
                    <button className="text-xs text-blue-600 hover:text-blue-800 mt-1">
                      {alert.action}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a
              href="/purchase/orders"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ShoppingCartIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">New Purchase Order</p>
                <p className="text-xs text-gray-500">Create order</p>
              </div>
            </a>
            
            <a
              href="/general/journals"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <DocumentTextIcon className="h-8 w-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Journal Entry</p>
                <p className="text-xs text-gray-500">Post entry</p>
              </div>
            </a>
            
            <a
              href="/stock/takes"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <CubeIcon className="h-8 w-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Stock Take</p>
                <p className="text-xs text-gray-500">Count inventory</p>
              </div>
            </a>
            
            <a
              href="/general/reports"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <ChartBarIcon className="h-8 w-8 text-red-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Financial Reports</p>
                <p className="text-xs text-gray-500">View reports</p>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}