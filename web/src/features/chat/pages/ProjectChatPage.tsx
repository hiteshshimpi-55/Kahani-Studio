import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { useProject } from '@/features/projects/hooks/use-project'

import { ChatComposer } from '../components/ChatComposer'
import { ChatEmptyState } from '../components/ChatEmptyState'
import { ChatMessageList } from '../components/ChatMessageList'
import { useAgentChat } from '../hooks/use-agent-chat'

export function ProjectChatPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const {
    messages,
    hydrating,
    streaming,
    error: chatError,
    send,
    attach,
    saveDraft,
    updateDraft,
  } = useAgentChat(projectId)
  const [uploading, setUploading] = useState(false)
  const empty = !hydrating && messages.length === 0

  if (loading || hydrating) {
    return (
      <div className="flex h-full items-center justify-center">
        <KissaLoader label="Opening chat…" />
      </div>
    )
  }

  if (error || !project || !projectId) {
    return (
      <div className="flex h-full items-center justify-center text-[13px] text-destructive">
        {error || 'Project not found'}
      </div>
    )
  }

  if (empty) {
    return (
      <ChatEmptyState
        isStreaming={streaming}
        onSend={send}
        onAttach={async (file) => {
          await attach(file)
        }}
      />
    )
  }

  return (
    <div className="chat-thread flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <ChatMessageList
          messages={messages}
          projectId={projectId}
          streaming={streaming}
          onSaveDraft={saveDraft}
          onUpdateDraft={updateDraft}
        />
      </div>
      <div className="relative z-10 mx-auto w-full max-w-[760px] shrink-0 bg-gradient-to-t from-[var(--surface-2)] via-[var(--surface-2)] to-transparent px-4 pt-5 pb-4 md:px-6">
        {chatError ? (
          <p className="mb-2 text-center text-[12px] text-destructive">{chatError}</p>
        ) : null}
        <ChatComposer
          isStreaming={streaming}
          isUploading={uploading}
          onSend={send}
          onAttach={async (file) => {
            setUploading(true)
            try {
              await attach(file)
            } finally {
              setUploading(false)
            }
          }}
        />
      </div>
    </div>
  )
}
