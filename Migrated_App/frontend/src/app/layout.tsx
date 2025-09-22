import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ACAS Migrated - Modern Accounting System',
  description: 'Modernized version of Applewood Computers Accounting System',
  keywords: ['accounting', 'ERP', 'business management', 'financial software'],
  authors: [{ name: 'ACAS Development Team' }],
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-neutral-50 text-secondary-900 antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}