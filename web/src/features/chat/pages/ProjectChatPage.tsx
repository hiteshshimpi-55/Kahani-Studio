import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { useProject } from '@/features/projects/hooks/use-project'

import { ChatComposer } from '../components/ChatComposer'
import { ChatEmptyState } from '../components/ChatEmptyState'
import { ChatMessageList } from '../components/ChatMessageList'
import { ChatSessionsPanel } from '../components/ChatSessionsPanel'
import { useAgentChat } from '../hooks/use-agent-chat'

export function ProjectChatPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { project, loading, error } = useProject(projectId)
  const {
    messages,
    sessions,
    activeSessionId,
    hydrating,
    streaming,
    error: chatError,
    send,
    stop,
    attach,
    saveDraft,
    updateDraft,
    resetSession,
    selectSession,
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

  return (
    <div className="flex h-full min-h-0">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-end gap-2 border-b border-[var(--folio-border)] px-4 py-2 lg:hidden">
          <button
            type="button"
            disabled={streaming}
            onClick={() => void resetSession()}
            className="rounded-[6px] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] disabled:opacity-40"
          >
            Reset session
          </button>
        </div>
        {empty ? (
          <ChatEmptyState
            isStreaming={streaming}
            onSend={send}
            onStop={stop}
            onAttach={async (file) => {
              await attach(file)
            }}
          />
        ) : (
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
                onStop={stop}
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
        )}
      </div>

      <ChatSessionsPanel
        sessions={sessions}
        activeSessionId={activeSessionId}
        streaming={streaming}
        onSelect={(id) => void selectSession(id)}
        onReset={() => void resetSession()}
      />
    </div>
  )
}
