'use client'

import MainLayout from '@/components/layout/main-layout'
import { AuthGuard } from '@/lib/auth/guard'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
        </div>
      }
    >
      <MainLayout>{children}</MainLayout>
    </AuthGuard>
  )
}