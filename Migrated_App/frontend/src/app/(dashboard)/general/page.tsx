'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  DocumentTextIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CalculatorIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline'

const generalModules = [
  {
    name: 'Chart of Accounts',
    description: 'Manage general ledger accounts',
    href: '/general/accounts',
    icon: ClipboardDocumentListIcon,
    color: 'bg-blue-500',
    stats: '1,247 Active Accounts'
  },
  {
    name: 'Journal Entries',
    description: 'Post journal entries and adjustments',
    href: '/general/journals',
    icon: DocumentTextIcon,
    color: 'bg-green-500',
    stats: '89 Entries This Month'
  },
  {
    name: 'GL Batches',
    description: 'Batch processing of transactions',
    href: '/general/batches',
    icon: DocumentTextIcon,
    color: 'bg-yellow-500',
    stats: '12 Batches Pending'
  },
  {
    name: 'Financial Reports',
    description: 'Generate financial statements',
    href: '/general/reports',
    icon: ChartBarIcon,
    color: 'bg-purple-500',
    stats: 'P&L, Balance Sheet, Trial Balance'
  },
  {
    name: 'Budgets',
    description: 'Budget planning and variance analysis',
    href: '/general/budgets',
    icon: CalculatorIcon,
    color: 'bg-indigo-500',
    stats: '2024 Budget Active'
  }
]

export default function GeneralLedgerPage() {
  return (
    <div>
      <PageHeader
        title="General Ledger"
        description="Chart of accounts and financial reporting"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ClipboardDocumentListIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">1,247</p>
                <p className="text-sm text-gray-600">GL Accounts</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">89</p>
                <p className="text-sm text-gray-600">Journal Entries</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$4.2M</p>
                <p className="text-sm text-gray-600">Total Assets</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$450K</p>
                <p className="text-sm text-gray-600">Net Income YTD</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {generalModules.map((module) => (
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