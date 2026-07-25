import { useEffect, useState } from 'react'

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
  onAttach?: (file: File) => void | Promise<void>
  isStreaming?: boolean
}

export function ChatEmptyState({ onSend, onAttach, isStreaming }: Props) {
  const [uploading, setUploading] = useState(false)
  const [headlineIndex, setHeadlineIndex] = useState(0)
  const [display, setDisplay] = useState('')
  const [phase, setPhase] = useState<'typing' | 'deleting'>('typing')

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

        <div className="mt-8 w-full max-w-[680px]">
          <ChatComposer
            variant="hero"
            isStreaming={isStreaming}
            isUploading={uploading}
            onSend={onSend}
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
