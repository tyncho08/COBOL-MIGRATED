'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  CubeIcon,
  TruckIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

const stockModules = [
  {
    name: 'Stock Items',
    description: 'Manage inventory and stock master data',
    href: '/stock/items',
    icon: CubeIcon,
    color: 'bg-blue-500',
    stats: '2,847 Items in Stock'
  },
  {
    name: 'Stock Movements',
    description: 'Track inventory transactions',
    href: '/stock/movements',
    icon: TruckIcon,
    color: 'bg-green-500',
    stats: '156 Movements Today'
  },
  {
    name: 'Stock Takes',
    description: 'Physical inventory counting',
    href: '/stock/takes',
    icon: DocumentTextIcon,
    color: 'bg-yellow-500',
    stats: '3 Counts in Progress'
  },
  {
    name: 'Stock Reports',
    description: 'Inventory analysis and reports',
    href: '/stock/reports',
    icon: ChartBarIcon,
    color: 'bg-purple-500',
    stats: 'Last Updated: Today'
  }
]

export default function StockControlPage() {
  return (
    <div>
      <PageHeader
        title="Stock Control"
        description="Inventory management and valuation"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CubeIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">2,847</p>
                <p className="text-sm text-gray-600">Stock Items</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <TruckIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">156</p>
                <p className="text-sm text-gray-600">Movements Today</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$2.1M</p>
                <p className="text-sm text-gray-600">Total Stock Value</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">23</p>
                <p className="text-sm text-gray-600">Below Reorder Level</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {stockModules.map((module) => (
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