'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, endpoints, setAccessToken, getAccessToken } from '@/lib/api/client'

interface User {
  id: number
  username: string
  full_name: string
  email: string
  is_active: boolean
  is_superuser: boolean
  user_level: number
  module_access: Record<string, number>
  allowed_companies: string[]
}

interface UserPermissions {
  user_id: number
  username: string
  is_superuser: boolean
  user_level: number
  module_access: Record<string, number>
  permissions: {
    sales: ModulePermission
    purchase: ModulePermission
    stock: ModulePermission
    general: ModulePermission
    system: ModulePermission
  }
}

interface ModulePermission {
  level: number
  can_view: boolean
  can_edit: boolean
  can_delete: boolean
  can_close?: boolean
  can_admin?: boolean
}

interface AuthContextType {
  user: User | null
  permissions: UserPermissions | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
  hasPermission: (module: string, level: number) => boolean
  canView: (module: string) => boolean
  canEdit: (module: string) => boolean
  canDelete: (module: string) => boolean
  canClose: (module: string) => boolean
  isAdmin: () => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [permissions, setPermissions] = useState<UserPermissions | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user && !!getAccessToken()

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')
      if (token) {
        setAccessToken(token)
        try {
          await loadUserData()
        } catch (error) {
          console.error('Failed to load user data:', error)
          logout()
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  // Auto-refresh token
  useEffect(() => {
    if (isAuthenticated) {
      const interval = setInterval(async () => {
        try {
          await refreshToken()
        } catch (error) {
          console.error('Token refresh failed:', error)
          logout()
        }
      }, 14 * 60 * 1000) // Refresh every 14 minutes

      return () => clearInterval(interval)
    }
  }, [isAuthenticated])

  const loadUserData = async () => {
    try {
      const [userData, permissionsData] = await Promise.all([
        api.get<User>(endpoints.auth.me),
        api.get<UserPermissions>(endpoints.auth.permissions)
      ])
      
      setUser(userData)
      setPermissions(permissionsData)
    } catch (error) {
      throw error
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post<{
        access_token: string
        refresh_token?: string
        token_type: string
        user: any
      }>(endpoints.auth.login, {
        username,
        password
      })

      // Store tokens
      localStorage.setItem('access_token', response.access_token)
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token)
      }
      setAccessToken(response.access_token)

      // Load user data
      await loadUserData()

      toast.success('Login successful!')
    } catch (error: any) {
      console.error('Login error:', error)
      
      if (error.response?.status === 401) {
        toast.error('Invalid username or password')
      } else if (error.response?.status === 403) {
        toast.error('Account is inactive')
      } else {
        toast.error('Login failed. Please try again.')
      }
      
      throw error
    }
  }

  const logout = () => {
    try {
      // Call logout endpoint if authenticated
      if (isAuthenticated) {
        api.post(endpoints.auth.logout).catch(console.error)
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear tokens and user data
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setAccessToken(null)
      setUser(null)
      setPermissions(null)
      
      // Redirect to login
      router.push('/login')
    }
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenStr = localStorage.getItem('refresh_token')
      if (!refreshTokenStr) {
        throw new Error('No refresh token available')
      }

      const response = await api.post<{
        access_token: string
        refresh_token: string
        token_type: string
      }>(endpoints.auth.refresh, { refresh_token: refreshTokenStr })

      // Update stored tokens
      localStorage.setItem('access_token', response.access_token)
      setAccessToken(response.access_token)

      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      return false
    }
  }

  // Permission checking functions
  const hasPermission = (module: string, level: number): boolean => {
    if (!permissions) return false
    if (permissions.is_superuser) return true
    
    const userLevel = permissions.module_access[module] || 0
    return userLevel >= level
  }

  const canView = (module: string): boolean => {
    if (!permissions) return false
    if (permissions.is_superuser) return true
    
    switch (module) {
      case 'sales':
        return permissions.permissions.sales.can_view
      case 'purchase':
        return permissions.permissions.purchase.can_view
      case 'stock':
        return permissions.permissions.stock.can_view
      case 'general':
        return permissions.permissions.general.can_view
      case 'system':
        return permissions.permissions.system.can_view
      default:
        return false
    }
  }

  const canEdit = (module: string): boolean => {
    if (!permissions) return false
    if (permissions.is_superuser) return true
    
    switch (module) {
      case 'sales':
        return permissions.permissions.sales.can_edit
      case 'purchase':
        return permissions.permissions.purchase.can_edit
      case 'stock':
        return permissions.permissions.stock.can_edit
      case 'general':
        return permissions.permissions.general.can_edit
      case 'system':
        return permissions.permissions.system.can_edit
      default:
        return false
    }
  }

  const canDelete = (module: string): boolean => {
    if (!permissions) return false
    if (permissions.is_superuser) return true
    
    switch (module) {
      case 'sales':
        return permissions.permissions.sales.can_delete
      case 'purchase':
        return permissions.permissions.purchase.can_delete
      case 'stock':
        return permissions.permissions.stock.can_delete
      case 'general':
        return permissions.permissions.general.can_delete
      case 'system':
        return permissions.permissions.system.can_delete
      default:
        return false
    }
  }

  const canClose = (module: string): boolean => {
    if (!permissions) return false
    if (permissions.is_superuser) return true
    
    switch (module) {
      case 'sales':
        return permissions.permissions.sales.can_close || false
      case 'purchase':
        return permissions.permissions.purchase.can_close || false
      case 'stock':
        return permissions.permissions.stock.can_close || false
      case 'general':
        return permissions.permissions.general.can_close || false
      default:
        return false
    }
  }

  const isAdmin = (): boolean => {
    if (!permissions) return false
    return permissions.is_superuser || permissions.permissions.system.can_admin || false
  }

  const value: AuthContextType = {
    user,
    permissions,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    hasPermission,
    canView,
    canEdit,
    canDelete,
    canClose,
    isAdmin,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider