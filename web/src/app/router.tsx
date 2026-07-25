import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { ProjectDetailPage } from '@/features/projects/pages/ProjectDetailPage'
import { ProjectsPage } from '@/features/projects/pages/ProjectsPage'
import { ScriptLatestPage } from '@/features/projects/pages/ScriptLatestPage'
import { SystemStatusPage } from '@/features/system/pages/SystemStatusPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <ProjectDetailPage /> },
      { path: 'projects/:projectId/scripts/latest', element: <ScriptLatestPage /> },
      { path: 'system', element: <SystemStatusPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])
