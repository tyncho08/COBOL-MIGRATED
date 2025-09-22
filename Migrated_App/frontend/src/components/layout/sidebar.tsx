'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'
import {
  HomeIcon,
  DocumentTextIcon,
  ShoppingCartIcon,
  TruckIcon,
  CubeIcon,
  ChartBarIcon,
  CogIcon,
  UsersIcon,
  BuildingStorefrontIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'

interface NavigationItem {
  name: string
  href?: string
  icon: any
  children?: NavigationItem[]
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  {
    name: 'Sales Ledger',
    icon: DocumentTextIcon,
    children: [
      { name: 'Sales Orders', href: '/sales/orders', icon: DocumentTextIcon },
      { name: 'Sales Invoices', href: '/sales/invoices', icon: DocumentTextIcon },
      { name: 'Customer Payments', href: '/sales/payments', icon: DocumentTextIcon },
      { name: 'Customer Statements', href: '/sales/statements', icon: DocumentTextIcon },
    ]
  },
  {
    name: 'Purchase Ledger',
    icon: ShoppingCartIcon,
    children: [
      { name: 'Purchase Orders', href: '/purchase/orders', icon: DocumentTextIcon },
      { name: 'Goods Receipts', href: '/purchase/receipts', icon: TruckIcon },
      { name: 'Purchase Invoices', href: '/purchase/invoices', icon: DocumentTextIcon },
      { name: 'Supplier Payments', href: '/purchase/payments', icon: DocumentTextIcon },
    ]
  },
  {
    name: 'Stock Control',
    icon: CubeIcon,
    children: [
      { name: 'Stock Items', href: '/stock/items', icon: CubeIcon },
      { name: 'Stock Movements', href: '/stock/movements', icon: TruckIcon },
      { name: 'Stock Takes', href: '/stock/takes', icon: DocumentTextIcon },
      { name: 'Stock Reports', href: '/stock/reports', icon: ChartBarIcon },
    ]
  },
  {
    name: 'General Ledger',
    icon: ChartBarIcon,
    children: [
      { name: 'Chart of Accounts', href: '/general/accounts', icon: DocumentTextIcon },
      { name: 'Journal Entries', href: '/general/journals', icon: DocumentTextIcon },
      { name: 'GL Batches', href: '/general/batches', icon: DocumentTextIcon },
      { name: 'Financial Reports', href: '/general/reports', icon: ChartBarIcon },
      { name: 'Budgets', href: '/general/budgets', icon: ChartBarIcon },
    ]
  },
  {
    name: 'Master Data',
    icon: UsersIcon,
    children: [
      { name: 'Suppliers', href: '/master/suppliers', icon: BuildingStorefrontIcon },
      { name: 'Customers', href: '/master/customers', icon: UsersIcon },
    ]
  },
  {
    name: 'System',
    icon: CogIcon,
    children: [
      { name: 'Periods', href: '/system/periods', icon: DocumentTextIcon },
      { name: 'Configuration', href: '/system/config', icon: CogIcon },
      { name: 'Audit Trail', href: '/system/audit', icon: DocumentTextIcon },
    ]
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpanded = (itemName: string) => {
    setExpandedItems(prev =>
      prev.includes(itemName)
        ? prev.filter(name => name !== itemName)
        : [...prev, itemName]
    )
  }

  const isExpanded = (itemName: string) => expandedItems.includes(itemName)

  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    const hasChildren = item.children && item.children.length > 0
    const isActive = item.href === pathname
    const expanded = isExpanded(item.name)

    if (hasChildren) {
      return (
        <div key={item.name}>
          <button
            onClick={() => toggleExpanded(item.name)}
            className={clsx(
              'group flex w-full items-center rounded-md py-2 pl-2 text-sm font-medium',
              level === 0 ? 'text-gray-300 hover:bg-gray-700 hover:text-white' : 'text-gray-400 hover:text-gray-300',
              'focus:outline-none focus:ring-2 focus:ring-white'
            )}
          >
            <item.icon
              className="mr-3 h-5 w-5 flex-shrink-0"
              aria-hidden="true"
            />
            <span className="flex-1">{item.name}</span>
            {expanded ? (
              <ChevronDownIcon className="ml-3 h-4 w-4" />
            ) : (
              <ChevronRightIcon className="ml-3 h-4 w-4" />
            )}
          </button>
          {expanded && (
            <div className="ml-6 mt-1 space-y-1">
              {item.children.map(child => renderNavigationItem(child, level + 1))}
            </div>
          )}
        </div>
      )
    }

    return (
      <Link
        key={item.href}
        href={item.href!}
        className={clsx(
          isActive
            ? 'bg-gray-900 text-white'
            : level === 0
            ? 'text-gray-300 hover:bg-gray-700 hover:text-white'
            : 'text-gray-400 hover:text-gray-300',
          'group flex items-center rounded-md py-2 pl-2 text-sm font-medium'
        )}
      >
        <item.icon
          className={clsx(
            isActive ? 'text-gray-300' : 'text-gray-400 group-hover:text-gray-300',
            'mr-3 h-5 w-5 flex-shrink-0'
          )}
          aria-hidden="true"
        />
        {item.name}
      </Link>
    )
  }

  return (
    <div className="flex h-full w-64 flex-col bg-gray-800">
      <div className="flex h-16 flex-shrink-0 items-center px-4">
        <h1 className="text-xl font-bold text-white">ACAS</h1>
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto">
        <nav className="flex-1 space-y-1 px-2 py-4">
          {navigation.map(item => renderNavigationItem(item))}
        </nav>
      </div>
    </div>
  )
}