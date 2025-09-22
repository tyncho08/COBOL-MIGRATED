'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  DocumentTextIcon,
  ShoppingCartIcon,
  TruckIcon,
  CurrencyDollarIcon,
  BuildingStorefrontIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const purchaseModules = [
  {
    name: 'Purchase Orders',
    description: 'Create and manage supplier orders',
    href: '/purchase/orders',
    icon: ShoppingCartIcon,
    color: 'bg-blue-500',
    stats: '89 Active Orders'
  },
  {
    name: 'Goods Receipts',
    description: 'Record incoming deliveries',
    href: '/purchase/receipts',
    icon: TruckIcon,
    color: 'bg-green-500',
    stats: '34 Pending Receipts'
  },
  {
    name: 'Purchase Invoices',
    description: 'Process supplier invoices',
    href: '/purchase/invoices',
    icon: DocumentTextIcon,
    color: 'bg-yellow-500',
    stats: '67 Awaiting Processing'
  },
  {
    name: 'Supplier Payments',
    description: 'Manage supplier payments',
    href: '/purchase/payments',
    icon: CurrencyDollarIcon,
    color: 'bg-purple-500',
    stats: '$78,450 Due This Week'
  }
]

export default function PurchaseLedgerPage() {
  return (
    <div>
      <PageHeader
        title="Purchase Ledger"
        description="Supplier management, purchasing, and payables"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <BuildingStorefrontIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">89</p>
                <p className="text-sm text-gray-600">Active Suppliers</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ShoppingCartIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">89</p>
                <p className="text-sm text-gray-600">Purchase Orders</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$95K</p>
                <p className="text-sm text-gray-600">Monthly Spend</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">12</p>
                <p className="text-sm text-gray-600">Pending Approvals</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {purchaseModules.map((module) => (
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