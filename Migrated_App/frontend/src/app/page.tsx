import Link from 'next/link'
import { 
  ChartBarIcon, 
  CurrencyDollarIcon, 
  ShoppingCartIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  CogIcon 
} from '@heroicons/react/24/outline'

const modules = [
  {
    name: 'Sales Ledger',
    description: 'Customer management, invoicing, and receivables',
    icon: CurrencyDollarIcon,
    href: '/sales',
    color: 'bg-blue-500',
  },
  {
    name: 'Purchase Ledger',
    description: 'Supplier management, purchasing, and payables',
    icon: ShoppingCartIcon,
    href: '/purchase',
    color: 'bg-purple-500',
  },
  {
    name: 'Stock Control',
    description: 'Inventory management and valuation',
    icon: BuildingOfficeIcon,
    href: '/stock',
    color: 'bg-green-500',
  },
  {
    name: 'General Ledger',
    description: 'Chart of accounts and financial reporting',
    icon: ChartBarIcon,
    href: '/general',
    color: 'bg-yellow-500',
  },
  {
    name: 'IRS System',
    description: 'Tax compliance and reporting',
    icon: DocumentTextIcon,
    href: '/irs',
    color: 'bg-red-500',
  },
  {
    name: 'System Admin',
    description: 'Users, settings, and configuration',
    icon: CogIcon,
    href: '/system',
    color: 'bg-gray-500',
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-secondary-900 sm:text-5xl">
            ACAS Migrated
          </h1>
          <p className="mt-3 text-xl text-secondary-600">
            Modern Accounting System for the 21st Century
          </p>
          <p className="mt-2 text-sm text-secondary-500">
            Powered by 45+ years of accounting excellence
          </p>
        </div>

        {/* Login Button */}
        <div className="mt-10 flex justify-center">
          <Link
            href="/login"
            className="btn-primary text-lg px-8 py-3 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
          >
            Access System
          </Link>
        </div>

        {/* Modules Grid */}
        <div className="mt-16">
          <h2 className="text-center text-2xl font-semibold text-secondary-800 mb-8">
            Integrated Business Modules
          </h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {modules.map((module) => (
              <div
                key={module.name}
                className="card hover:shadow-lg transition-shadow duration-300"
              >
                <div className="p-6">
                  <div className="flex items-center">
                    <div className={`${module.color} p-3 rounded-lg`}>
                      <module.icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="ml-4 text-lg font-medium text-secondary-900">
                      {module.name}
                    </h3>
                  </div>
                  <p className="mt-4 text-sm text-secondary-600">
                    {module.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="mt-16">
          <h2 className="text-center text-2xl font-semibold text-secondary-800 mb-8">
            Enterprise-Grade Features
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">100%</div>
              <div className="text-sm text-secondary-600">COBOL Feature Parity</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">Real-time</div>
              <div className="text-sm text-secondary-600">Financial Reporting</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">Multi-user</div>
              <div className="text-sm text-secondary-600">Concurrent Access</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">Secure</div>
              <div className="text-sm text-secondary-600">Role-based Access</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-secondary-500">
          <p>© 2024 ACAS Migrated. Built on decades of accounting expertise.</p>
          <p className="mt-2">
            Migration from COBOL/GnuCOBOL to modern Python/Next.js stack
          </p>
        </footer>
      </div>
    </div>
  )
}