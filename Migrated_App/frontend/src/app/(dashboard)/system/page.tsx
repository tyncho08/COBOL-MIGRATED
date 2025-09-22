'use client'

import Link from 'next/link'
import { PageHeader } from '@/components/business/page-header'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  CogIcon,
  DocumentTextIcon,
  ClockIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

const systemModules = [
  {
    name: 'Periods',
    description: 'Manage accounting periods and fiscal calendar',
    href: '/system/periods',
    icon: ClockIcon,
    color: 'bg-blue-500',
    stats: 'Period 12/2024 Active'
  },
  {
    name: 'Configuration',
    description: 'System settings and parameters',
    href: '/system/config',
    icon: CogIcon,
    color: 'bg-green-500',
    stats: 'Last Updated: Today'
  },
  {
    name: 'Audit Trail',
    description: 'System activity and transaction logs',
    href: '/system/audit',
    icon: ShieldCheckIcon,
    color: 'bg-purple-500',
    stats: '1,247 Entries Today'
  }
]

export default function SystemPage() {
  return (
    <div>
      <PageHeader
        title="System Administration"
        description="System configuration, periods, and audit management"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">12/2024</p>
                <p className="text-sm text-gray-600">Current Period</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">1,247</p>
                <p className="text-sm text-gray-600">Audit Entries Today</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">99.9%</p>
                <p className="text-sm text-gray-600">System Uptime</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold text-gray-900">0</p>
                <p className="text-sm text-gray-600">System Alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {systemModules.map((module) => (
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

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database Connection</span>
                <div className="flex items-center">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">Online</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Services</span>
                <div className="flex items-center">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">Running</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Background Jobs</span>
                <div className="flex items-center">
                  <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Storage Space</span>
                <div className="flex items-center">
                  <CheckCircleIcon className="h-4 w-4 text-yellow-500 mr-1" />
                  <span className="text-sm text-yellow-600">78% Used</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent System Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <CogIcon className="h-5 w-5 text-blue-600" />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">System configuration updated</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <ClockIcon className="h-5 w-5 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">Period 11/2024 closed successfully</p>
                  <p className="text-xs text-gray-500">1 day ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">User admin logged in from 192.168.1.100</p>
                  <p className="text-xs text-gray-500">3 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <DocumentTextIcon className="h-5 w-5 text-yellow-600" />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">Database backup completed</p>
                  <p className="text-xs text-gray-500">Last night</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}