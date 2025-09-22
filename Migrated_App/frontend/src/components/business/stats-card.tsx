import { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { clsx } from 'clsx'

interface StatsCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    type: 'increase' | 'decrease'
    period: string
  }
  icon?: ReactNode
  trend?: 'up' | 'down' | 'neutral'
  loading?: boolean
}

export function StatsCard({ 
  title, 
  value, 
  change, 
  icon, 
  trend = 'neutral', 
  loading = false 
}: StatsCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/3"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-semibold text-gray-900">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            {change && (
              <div className="flex items-center mt-2">
                <span
                  className={clsx(
                    'text-sm font-medium',
                    change.type === 'increase' ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  {change.type === 'increase' ? '+' : '-'}{Math.abs(change.value)}%
                </span>
                <span className="text-sm text-gray-500 ml-2">
                  from {change.period}
                </span>
              </div>
            )}
          </div>
          {icon && (
            <div className={clsx(
              'p-3 rounded-full',
              trend === 'up' && 'bg-green-100 text-green-600',
              trend === 'down' && 'bg-red-100 text-red-600',
              trend === 'neutral' && 'bg-blue-100 text-blue-600'
            )}>
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}