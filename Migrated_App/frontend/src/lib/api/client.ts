import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'

// API Client Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1'

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management
let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete apiClient.defaults.headers.common['Authorization']
  }
}

export const getAccessToken = () => accessToken

// Initialize token from localStorage on load
if (typeof window !== 'undefined') {
  const storedToken = localStorage.getItem('token')
  if (storedToken) {
    setAccessToken(storedToken)
  }
}

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage for each request
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
    }
    
    // Add timestamp to prevent caching
    config.params = {
      ...config.params,
      _t: Date.now(),
    }
    
    // Log requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`, config.data)
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log responses in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ Response:`, response.data)
    }
    return response
  },
  async (error: AxiosError) => {
    const { response, config } = error
    
    // Handle specific error codes
    if (response?.status === 401) {
      // Unauthorized - redirect to login
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        toast.error('Session expired. Please login again.')
        window.location.href = '/login'
      }
    } else if (response?.status === 403) {
      // Forbidden
      toast.error('You do not have permission to perform this action.')
    } else if (response?.status === 404) {
      // Not found
      toast.error('The requested resource was not found.')
    } else if (response?.status === 422) {
      // Validation error
      const errors = (response.data as any)?.detail
      if (Array.isArray(errors)) {
        errors.forEach(err => {
          toast.error(`${err.loc.join('.')}: ${err.msg}`)
        })
      } else {
        toast.error('Validation error. Please check your input.')
      }
    } else if (response?.status === 500) {
      // Server error
      toast.error('An unexpected error occurred. Please try again later.')
    } else if (!response) {
      // Network error
      toast.error('Network error. Please check your connection.')
    }
    
    // Log errors in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`❌ Error:`, error)
    }
    
    return Promise.reject(error)
  }
)

// Generic API methods
export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) => 
    apiClient.get<T>(url, config).then(res => res.data),
    
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.post<T>(url, data, config).then(res => res.data),
    
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.put<T>(url, data, config).then(res => res.data),
    
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.patch<T>(url, data, config).then(res => res.data),
    
  delete: <T = any>(url: string, config?: AxiosRequestConfig) => 
    apiClient.delete<T>(url, config).then(res => res.data),
}

// Specific API endpoints
export const endpoints = {
  // Auth
  auth: {
    login: '/auth/token',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    me: '/auth/me',
    permissions: '/auth/permissions',
    changePassword: '/auth/change-password',
  },
  
  // Sales
  sales: {
    customers: '/sales/customers',
    invoices: '/sales/invoices',
    orders: '/sales/orders',
    payments: '/sales/payments',
    reports: '/sales/reports',
  },
  
  // Purchase
  purchase: {
    suppliers: '/purchase/suppliers',
    orders: '/purchase/orders',
    invoices: '/purchase/invoices',
    payments: '/purchase/payments',
    reports: '/purchase/reports',
  },
  
  // Stock
  stock: {
    items: '/stock/items',
    movements: '/stock/movements',
    valuation: '/stock/valuation',
    reorder: '/stock/reorder',
    reports: '/stock/reports',
  },
  
  // General Ledger
  general: {
    accounts: '/general/accounts',
    journals: '/general/journals',
    periods: '/general/periods',
    reports: '/general/reports',
  },
  
  // IRS
  irs: {
    forms: '/irs/forms',
    filings: '/irs/filings',
    calculations: '/irs/calculations',
    reports: '/irs/reports',
  },
  
  // System
  system: {
    users: '/system/users',
    config: '/system/config',
    audit: '/system/audit',
    backup: '/system/backup',
  },
}