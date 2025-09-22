'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  DocumentTextIcon,
  CurrencyDollarIcon,
  UsersIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const salesModules = [
  {
    name: 'Sales Orders',
    description: 'Create and manage customer orders',
    href: '/sales/orders',
    icon: DocumentTextIcon,
    color: 'bg-blue-500',
    stats: '156 Active Orders'
  },
  {
    name: 'Sales Invoices',
    description: 'Generate and manage invoices',
    href: '/sales/invoices',
    icon: DocumentTextIcon,
    color: 'bg-green-500',
    stats: '89 Pending Invoices'
  },
  {
    name: 'Customer Payments',
    description: 'Track and process payments',
    href: '/sales/payments',
    icon: CurrencyDollarIcon,
    color: 'bg-yellow-500',
    stats: '$45,230 Outstanding'
  },
  {
    name: 'Customer Statements',
    description: 'Generate customer statements',
    href: '/sales/statements',
    icon: ChartBarIcon,
    color: 'bg-purple-500',
    stats: '23 Overdue Accounts'
  }
]

export default function SalesLedgerPage() {
  return (
    <div>
      <PageHeader
        title="Sales Ledger"
        description="Customer management, invoicing, and receivables"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <UsersIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">247</p>
                <p className="text-sm text-gray-600">Active Customers</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">156</p>
                <p className="text-sm text-gray-600">Sales Orders</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$128K</p>
                <p className="text-sm text-gray-600">Monthly Revenue</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">23</p>
                <p className="text-sm text-gray-600">Overdue Accounts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {salesModules.map((module) => (
          <Link key={module.name} href={module.href}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <div className={`${module.color} p-3 rounded-lg`}>
                    <module.icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {module.name}
                    </h3>
                    <p className="text-sm text-gray-600">{module.description}</p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700">{module.stats}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}