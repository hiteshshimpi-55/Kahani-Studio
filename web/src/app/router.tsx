import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { ProjectChatPage } from '@/features/chat/pages/ProjectChatPage'
import { EditorPage } from '@/features/editor/pages/EditorPage'
import { ProjectContextPage } from '@/features/projects/pages/ProjectContextPage'
import { ProjectDraftsPage } from '@/features/projects/pages/ProjectDraftsPage'
import { ProjectVisualsPage } from '@/features/projects/pages/ProjectVisualsPage'
import { ProjectsPage } from '@/features/projects/pages/ProjectsPage'
import { SystemStatusPage } from '@/features/system/pages/SystemStatusPage'
import { VoiceLibraryPage } from '@/features/voices/pages/VoiceLibraryPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <Navigate to="chat" relative="path" replace /> },
      { path: 'projects/:projectId/chat', element: <ProjectChatPage /> },
      { path: 'projects/:projectId/context', element: <ProjectContextPage /> },
      {
        path: 'projects/:projectId/attachments',
        element: <Navigate to="../context" relative="path" replace />,
      },
      { path: 'projects/:projectId/drafts', element: <ProjectDraftsPage /> },
      {
        path: 'projects/:projectId/scripts/latest',
        element: <Navigate to="../drafts" relative="path" replace />,
      },
      { path: 'projects/:projectId/visuals', element: <ProjectVisualsPage /> },
      {
        path: 'projects/:projectId/editor',
        element: <Navigate to="/editor" replace />,
      },
      { path: 'editor', element: <EditorPage /> },
      { path: 'voices', element: <VoiceLibraryPage /> },
      { path: 'system', element: <SystemStatusPage /> },
      { path: 'settings/*', element: <Navigate to="/" replace /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])
