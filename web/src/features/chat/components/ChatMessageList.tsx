import { useEffect, useRef } from 'react'

import type { ChatMessage, PlotPitch } from '../types'
import { ChatActivityLine } from './ChatActivityLine'
import { PlotPitchCards } from './PlotPitchCards'
import { ScriptResultCard } from './ScriptResultCard'
import { StreamingText } from './StreamingText'

export function ChatMessageList({
  messages,
  projectId,
  streaming,
  onSaveDraft,
  onUpdateDraft,
  onPickPlot,
}: {
  messages: ChatMessage[]
  projectId: string
  streaming: boolean
  onSaveDraft?: (runId: string, messageId: string, text?: string) => void | Promise<void>
  onUpdateDraft?: (scriptId: string, messageId: string, text: string) => void | Promise<void>
  onPickPlot?: (pitch: PlotPitch) => void
}) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: streaming ? 'auto' : 'smooth',
      block: 'end',
    })
  }, [messages, streaming])

  return (
    <div className="mx-auto w-full max-w-[760px] space-y-7 px-4 py-6 md:px-6">
      {messages.map((message) => {
        const isUser = message.role === 'user'
        const isStreaming = message.status === 'streaming'

        return (
          <div key={message.id} className={isUser ? 'flex justify-end' : 'flex justify-start'}>
            <div
              className={
                isUser
                  ? 'max-w-[82%] rounded-[20px] bg-[var(--surface-1)] px-4 py-3 text-[14px] leading-6 text-[var(--text-primary)]'
                  : 'w-full max-w-[680px] text-[15px] leading-7 text-[var(--text-primary)]'
              }
            >
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <>
                  {isStreaming && message.activity && !message.content ? (
                    <ChatActivityLine activity={message.activity} />
                  ) : null}
                  {message.content ? (
                    <>
                      <StreamingText
                        text={message.content}
                        active={
                          isStreaming &&
                          !message.scriptPreview &&
                          !message.activity &&
                          !message.plotPitches?.length
                        }
                      />
                      {isStreaming && message.activity && message.kind === 'generating' ? (
                        <ChatActivityLine
                          activity={message.activity}
                          className="mt-3"
                        />
                      ) : null}
                    </>
                  ) : isStreaming && !message.activity ? (
                    <ChatActivityLine
                      activity={{ phase: 'thinking', label: 'Reading your message…' }}
                    />
                  ) : null}
                  {message.plotPitches && message.plotPitches.length > 0 ? (
                    <PlotPitchCards
                      pitches={message.plotPitches}
                      disabled={streaming}
                      onPick={(pitch) => onPickPlot?.(pitch)}
                    />
                  ) : null}
                  {message.scriptPreview ? (
                    <ScriptResultCard
                      projectId={projectId}
                      scriptId={message.scriptId}
                      runId={message.runId}
                      preview={message.scriptPreview}
                      isDraft={message.isDraft}
                      onSaveDraft={
                        message.runId && onSaveDraft
                          ? (text) => onSaveDraft(message.runId!, message.id, text)
                          : undefined
                      }
                      onUpdateDraft={
                        message.scriptId && onUpdateDraft
                          ? (text) => onUpdateDraft(message.scriptId!, message.id, text)
                          : undefined
                      }
                    />
                  ) : null}
                </>
              )}
            </div>
          </div>
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}
