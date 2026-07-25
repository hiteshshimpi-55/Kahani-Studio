import { ThemeProvider } from 'next-themes'
import type { ReactNode } from 'react'

import { ErrorBoundary } from '@/components/ErrorBoundary'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
        {children}
      </ThemeProvider>
    </ErrorBoundary>
  )
}
