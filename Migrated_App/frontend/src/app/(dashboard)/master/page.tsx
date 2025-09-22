'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  UsersIcon,
  BuildingStorefrontIcon,
  DocumentTextIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const masterDataModules = [
  {
    name: 'Customers',
    description: 'Customer master data and credit management',
    href: '/master/customers',
    icon: UsersIcon,
    color: 'bg-blue-500',
    stats: '247 Active Customers'
  },
  {
    name: 'Suppliers',
    description: 'Supplier master data and vendor management',
    href: '/master/suppliers',
    icon: BuildingStorefrontIcon,
    color: 'bg-green-500',
    stats: '89 Active Suppliers'
  }
]

export default function MasterDataPage() {
  return (
    <div>
      <PageHeader
        title="Master Data"
        description="Customer and supplier master data management"
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
              <BuildingStorefrontIcon className="h-8 w-8 text-green-600" />
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
              <DocumentTextIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">156</p>
                <p className="text-sm text-gray-600">Open Transactions</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">$2.1M</p>
                <p className="text-sm text-gray-600">Total Credit Limit</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {masterDataModules.map((module) => (
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

      {/* Recent Activity */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Recent Master Data Updates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <UsersIcon className="h-5 w-5 text-blue-600" />
              <div className="flex-1">
                <p className="text-sm text-gray-900">Customer ACME Corp credit limit updated to $50,000</p>
                <p className="text-xs text-gray-500">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <BuildingStorefrontIcon className="h-5 w-5 text-green-600" />
              <div className="flex-1">
                <p className="text-sm text-gray-900">New supplier Global Tech Solutions added</p>
                <p className="text-xs text-gray-500">1 day ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <UsersIcon className="h-5 w-5 text-blue-600" />
              <div className="flex-1">
                <p className="text-sm text-gray-900">Customer Smith Industries payment terms updated to Net 30</p>
                <p className="text-xs text-gray-500">2 days ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}