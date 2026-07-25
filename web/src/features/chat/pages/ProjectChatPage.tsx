import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { KissaLoader } from '@/components/ui/kissa-loader'
import { useProject } from '@/features/projects/hooks/use-project'
import { useStoryContextSummary } from '@/features/projects/hooks/use-story-context'
import { NotFoundView } from '@/features/system/pages/NotFoundPage'

import type { ChatMessage, PlotPitch } from '../types'
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
    addSession,
    selectSession,
  } = useAgentChat(projectId)
  const { summary, refresh: refreshContext } = useStoryContextSummary(projectId)
  const [uploading, setUploading] = useState(false)
  const empty = !hydrating && messages.length === 0

  useEffect(() => {
    if (!streaming) void refreshContext()
  }, [streaming, refreshContext])

  const handlePickPlot = (pitch: PlotPitch) => {
    void send(`Let's go with "${pitch.title}" — ${pitch.logline}`)
  }

  const handleContinue = (message: ChatMessage) => {
    const partNo = message.scriptPackage?.parts?.[0]?.part_number
    const cliff = message.scriptPackage?.parts?.[0]?.cliff_out
    const next = partNo != null ? partNo + 1 : undefined
    const prompt = next
      ? `Continue to episode ${next}.${cliff ? ` Pick up from this cliff: ${cliff}` : ''}`
      : `Continue to the next episode.${cliff ? ` Pick up from this cliff: ${cliff}` : ''}`
    void send(prompt.trim())
  }

  const contextChip =
    summary && (summary.cast_count > 0 || summary.docs_count > 0 || summary.episode_count > 0)
      ? [
          summary.cast_count ? `Cast ${summary.cast_count}` : null,
          summary.docs_count ? `Docs ${summary.docs_count}` : null,
          summary.latest_part_number != null
            ? `Ep.${summary.latest_part_number}`
            : summary.episode_count
              ? `Eps ${summary.episode_count}`
              : null,
        ]
          .filter(Boolean)
          .join(' · ')
      : null

  if (loading || hydrating) {
    return (
      <div className="flex h-full items-center justify-center">
        <KissaLoader label="Opening chat…" />
      </div>
    )
  }

  if (error || !project || !projectId) {
    return (
      <NotFoundView
        kind="project"
        detail={error && error !== 'Project not found' ? error : null}
      />
    )
  }

  return (
    <div className="flex h-full min-h-0">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-end gap-2 border-b border-[var(--folio-border)] px-4 py-2 lg:hidden">
          <button
            type="button"
            disabled={streaming}
            onClick={() => void addSession()}
            className="rounded-[6px] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] disabled:opacity-40"
          >
            Add session
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
                onPickPlot={handlePickPlot}
                onContinueEpisode={handleContinue}
              />
            </div>
            <div className="relative z-10 mx-auto w-full max-w-[760px] shrink-0 bg-gradient-to-t from-[var(--surface-2)] via-[var(--surface-2)] to-transparent px-4 pt-5 pb-4 md:px-6">
              {chatError ? (
                <p className="mb-2 text-center text-[12px] text-destructive">{chatError}</p>
              ) : null}
              <ChatComposer
                isStreaming={streaming}
                isUploading={uploading}
                contextChip={contextChip}
                contextHref={`/projects/${projectId}/context`}
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
        onAdd={() => void addSession()}
      />
    </div>
  )
}
