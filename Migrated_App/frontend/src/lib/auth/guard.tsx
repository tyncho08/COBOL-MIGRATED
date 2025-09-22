'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from './context'

interface AuthGuardProps {
  children: React.ReactNode
  requiredModule?: string
  requiredLevel?: number
  fallback?: React.ReactNode
}

/**
 * AuthGuard component that protects routes based on authentication status
 * and optional module permissions
 */
export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requiredModule,
  requiredLevel = 1, // Default to ENQUIRY level
  fallback = <div>Loading...</div>
}) => {
  const { user, isLoading, isAuthenticated, hasPermission } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  // Show loading while checking authentication
  if (isLoading) {
    return <>{fallback}</>
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return null
  }

  // Check module permissions if required
  if (requiredModule && !hasPermission(requiredModule, requiredLevel)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              Access Denied
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              You do not have sufficient permissions to access this module.
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Required: {requiredModule} (Level {requiredLevel})
            </p>
            <div className="mt-6">
              <button
                onClick={() => router.back()}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

interface PublicOnlyProps {
  children: React.ReactNode
}

/**
 * PublicOnly component that redirects authenticated users to dashboard
 * Used for login page, etc.
 */
export const PublicOnly: React.FC<PublicOnlyProps> = ({ children }) => {
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null
  }

  return <>{children}</>
}

interface PermissionWrapperProps {
  children: React.ReactNode
  module: string
  level?: number
  fallback?: React.ReactNode
}

/**
 * PermissionWrapper component that conditionally renders content based on permissions
 * Used for hiding/showing specific UI elements
 */
export const PermissionWrapper: React.FC<PermissionWrapperProps> = ({
  children,
  module,
  level = 1,
  fallback = null
}) => {
  const { hasPermission } = useAuth()

  if (!hasPermission(module, level)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

interface ModulePermissionProps {
  children: React.ReactNode
  module: string
  action: 'view' | 'edit' | 'delete' | 'close'
  fallback?: React.ReactNode
}

/**
 * ModulePermission component for specific action-based permissions
 */
export const ModulePermission: React.FC<ModulePermissionProps> = ({
  children,
  module,
  action,
  fallback = null
}) => {
  const { canView, canEdit, canDelete, canClose } = useAuth()

  let hasPermission = false

  switch (action) {
    case 'view':
      hasPermission = canView(module)
      break
    case 'edit':
      hasPermission = canEdit(module)
      break
    case 'delete':
      hasPermission = canDelete(module)
      break
    case 'close':
      hasPermission = canClose(module)
      break
  }

  if (!hasPermission) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

interface AdminOnlyProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

/**
 * AdminOnly component for system administration features
 */
export const AdminOnly: React.FC<AdminOnlyProps> = ({
  children,
  fallback = null
}) => {
  const { isAdmin } = useAuth()

  if (!isAdmin()) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

export default AuthGuard