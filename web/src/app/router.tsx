import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { SystemStatusPage } from '@/features/system/pages/SystemStatusPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <SystemStatusPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])
