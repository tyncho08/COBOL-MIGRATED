import { api } from '@/lib/api/client'

export interface GoodsReceipt {
  id?: number
  receipt_number?: string
  receipt_date: string
  supplier_id: number
  supplier_code: string
  supplier_name?: string
  order_number?: string
  delivery_note?: string
  receipt_status: 'PENDING' | 'PARTIAL' | 'RECEIVED' | 'CANCELLED'
  total_quantity: number
  total_value: number
  goods_received: number
  outstanding_quantity: number
  is_complete: boolean
  gl_posted: boolean
  received_by: string
  notes?: string
  created_date?: string
  posted_date?: string
}

export interface GoodsReceiptLine {
  id?: number
  line_number: number
  stock_code: string
  description: string
  quantity_received: number
  unit_cost: number
  line_total: number
  location?: string
  batch_number?: string
  serial_numbers?: string[]
}

export const goodsReceiptsApi = {
  // Get all goods receipts
  getAll: async (params?: { 
    status?: string
    supplier_id?: number
    date_from?: string
    date_to?: string
    posted?: boolean 
  }) => {
    const response = await api.get<GoodsReceipt[] | { data: GoodsReceipt[] }>('/purchase/receipts', { params })
    // Handle both wrapped and unwrapped responses
    return Array.isArray(response) ? response : (response.data || [])
  },
  
  // Get single goods receipt by ID
  getById: (id: number) => api.get<GoodsReceipt>(`/purchase/receipts/${id}`),
  
  // Create new goods receipt
  create: (data: Omit<GoodsReceipt, 'id' | 'receipt_number' | 'created_date'>) => 
    api.post<GoodsReceipt>('/purchase/receipts', data),
  
  // Update goods receipt
  update: (id: number, data: Partial<GoodsReceipt>) => 
    api.put<GoodsReceipt>(`/purchase/receipts/${id}`, data),
  
  // Delete goods receipt
  delete: (id: number) => api.delete(`/purchase/receipts/${id}`),
  
  // Post goods receipt to GL
  post: (id: number) => api.post(`/purchase/receipts/${id}/post`),
  
  // Cancel goods receipt
  cancel: (id: number) => api.post(`/purchase/receipts/${id}/cancel`),
  
  // Get receipt lines
  getLines: (receiptId: number) => api.get<GoodsReceiptLine[]>(`/purchase/receipts/${receiptId}/lines`),
  
  // Print receipt
  print: (id: number) => api.get(`/purchase/receipts/${id}/print`, { responseType: 'blob' }),
  
  // Get receipts for purchase order
  getByPurchaseOrder: (orderNumber: string) => 
    api.get<GoodsReceipt[]>(`/purchase/receipts/order/${orderNumber}`),
  
  // Get suggested receipts based on outstanding orders
  getSuggestions: (supplierId?: number) => 
    api.get(`/purchase/receipts/suggestions${supplierId ? `?supplier_id=${supplierId}` : ''}`),
}