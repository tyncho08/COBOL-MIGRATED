'use client'

import { ReactNode } from 'react'
import Header from './header'
import Sidebar from './sidebar'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        <Header />
        
        {/* Main content area */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-4 lg:py-6">
            <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 2xl:px-12">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}