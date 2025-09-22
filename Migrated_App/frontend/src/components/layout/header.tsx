'use client'

import { Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import { BellIcon, UserCircleIcon, PowerIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'
import { useAuth } from '@/lib/auth/context'
import Link from 'next/link'

export default function Header() {
  const { user, logout, permissions } = useAuth()

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="bg-white shadow">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h2 className="text-lg font-semibold text-gray-900">
                Applewood Computers Accounting System
              </h2>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* User info */}
            <div className="hidden md:flex md:items-center md:space-x-2">
              <span className="text-sm text-gray-500">Welcome,</span>
              <span className="text-sm font-medium text-gray-900">
                {user?.full_name || user?.username}
              </span>
              {user?.is_superuser && (
                <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                  Admin
                </span>
              )}
            </div>

            {/* Notifications */}
            <button
              type="button"
              className="rounded-full bg-white p-1 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <span className="sr-only">View notifications</span>
              <BellIcon className="h-6 w-6" aria-hidden="true" />
            </button>

            {/* Profile dropdown */}
            <Menu as="div" className="relative ml-3">
              <div>
                <Menu.Button className="flex max-w-xs items-center rounded-full bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 lg:rounded-md lg:p-2 lg:hover:bg-gray-50">
                  <UserCircleIcon className="h-8 w-8 text-gray-400" />
                  <span className="ml-3 hidden text-sm font-medium text-gray-700 lg:block">
                    {user?.username}
                  </span>
                </Menu.Button>
              </div>
              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  {/* User Info Section */}
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-sm text-gray-500">{user?.email}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Level {user?.user_level} {user?.is_superuser && '(Admin)'}
                    </p>
                  </div>


                  {/* Permissions Info */}
                  <Menu.Item>
                    {({ active }) => (
                      <div
                        className={clsx(
                          active ? 'bg-gray-100' : '',
                          'block px-4 py-2 text-sm text-gray-700 cursor-default'
                        )}
                      >
                        <div className="text-xs text-gray-500 mb-1">Module Access:</div>
                        <div className="grid grid-cols-2 gap-1 text-xs">
                          {permissions && Object.entries(permissions.permissions).map(([module, perms]) => (
                            <div key={module} className="flex justify-between">
                              <span className="capitalize">{module}:</span>
                              <span className="font-mono">{perms.level}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Menu.Item>

                  {/* Logout */}
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={handleLogout}
                        className={clsx(
                          active ? 'bg-gray-100' : '',
                          'flex w-full items-center px-4 py-2 text-sm text-gray-700'
                        )}
                      >
                        <PowerIcon className="mr-3 h-4 w-4" />
                        Sign out
                      </button>
                    )}
                  </Menu.Item>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>
    </div>
  )
}