import { useEffect, useRef, useState } from 'react'

import heroIllustration from '@/assets/ai-story-hero.svg'

import { ChatComposer } from './ChatComposer'

const PROMPTS = [
  'Write a 4-part Hindi thriller about a midnight house',
  'Pocket FM serial: rivals fall in love at a radio station',
  'Short horror: something knocks from inside the well',
]

const HEADLINES = [
  "Let's get your story published",
  'Ready when you are',
  'Tell me a story to hear',
  "Let's write the next episode",
  'What will they binge next?',
]

const TYPE_MS = 42
const DELETE_MS = 26
const HOLD_MS = 2400

type Props = {
  onSend: (text: string) => void | Promise<void>
  onStop?: () => void | Promise<void>
  onAttach?: (file: File) => void | Promise<void>
  isStreaming?: boolean
  initialPrompt?: string
}

export function ChatEmptyState({ onSend, onAttach, onStop, isStreaming, initialPrompt }: Props) {
  const [uploading, setUploading] = useState(false)
  const [headlineIndex, setHeadlineIndex] = useState(0)
  const [display, setDisplay] = useState('')
  const [phase, setPhase] = useState<'typing' | 'deleting'>('typing')
  const autoSentRef = useRef(false)

  // Auto-send when arriving from Discover with a pre-built prompt
  useEffect(() => {
    if (initialPrompt && !autoSentRef.current) {
      autoSentRef.current = true
      void onSend(initialPrompt)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const full = HEADLINES[headlineIndex]
    let timeout: number

    if (phase === 'typing') {
      if (display.length < full.length) {
        timeout = window.setTimeout(() => {
          setDisplay(full.slice(0, display.length + 1))
        }, TYPE_MS)
      } else {
        timeout = window.setTimeout(() => setPhase('deleting'), HOLD_MS)
      }
    } else if (display.length > 0) {
      timeout = window.setTimeout(() => {
        setDisplay(display.slice(0, -1))
      }, DELETE_MS)
    } else {
      setHeadlineIndex((i) => (i + 1) % HEADLINES.length)
      setPhase('typing')
    }

    return () => window.clearTimeout(timeout)
  }, [display, phase, headlineIndex])

  return (
    <div className="chat-atmosphere relative flex h-full min-h-0 flex-col">
      <div className="relative z-[1] flex flex-1 flex-col items-center justify-center px-4 pb-8">
        <h1 className="chat-typewriter-headline" aria-live="polite">
          <span className="chat-typewriter-line">{display || '\u00a0'}</span>
        </h1>

        <div className="mt-6 overflow-hidden rounded-[20px] border border-[var(--folio-border)] bg-[var(--surface-1)]/80 shadow-[0_18px_45px_rgba(15,23,42,0.12)] backdrop-blur">
          <img src={heroIllustration} alt="AI story studio illustration" className="h-44 w-full object-cover" />
          <div className="p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[var(--brand)]">
              Studio concept
            </p>
            <p className="mt-1 text-[13px] leading-6 text-[var(--text-secondary)]">
              Create a story seed, guide the agents, and let the draft evolve into a polished release.
            </p>
          </div>
        </div>

        <div className="mt-8 w-full max-w-[680px]">
          <ChatComposer
            variant="hero"
            isStreaming={isStreaming}
            isUploading={uploading}
            initialValue={initialPrompt}
            onSend={onSend}
            onStop={onStop}
            onAttach={async (file) => {
              if (!onAttach) return
              setUploading(true)
              try {
                await onAttach(file)
              } finally {
                setUploading(false)
              }
            }}
          />
        </div>

        <div className="mt-5 flex max-w-[720px] flex-wrap justify-center gap-2">
          {PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="chat-prompt-chip"
              disabled={isStreaming}
              onClick={() => void onSend(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
