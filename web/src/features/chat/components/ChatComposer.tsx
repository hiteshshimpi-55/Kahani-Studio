import { ArrowUp, Square } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { AddAssetMenu } from '@/components/AddAssetMenu'
import { cn } from '@/lib/utils'

type Props = {
  onSend: (text: string) => void | Promise<void>
  onStop?: () => void | Promise<void>
  onAttach?: (file: File) => void | Promise<void>
  isStreaming?: boolean
  isUploading?: boolean
  disabled?: boolean
  variant?: 'default' | 'hero'
  placeholder?: string
  contextChip?: ReactNode
  contextHref?: string
}

export function ChatComposer({
  onSend,
  onStop,
  onAttach,
  isStreaming = false,
  isUploading = false,
  disabled = false,
  variant = 'default',
  placeholder = 'Ask anything, or describe the story you want…',
  contextChip,
  contextHref,
}: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hero = variant === 'hero'

  const resize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, hero ? 220 : 160)}px`
  }, [hero])

  useEffect(() => {
    resize()
  }, [value, resize])

  const submit = async () => {
    const text = value.trim()
    if (!text || disabled || isStreaming) return
    setValue('')
    await onSend(text)
    requestAnimationFrame(() => textareaRef.current?.focus())
  }

  // Allow typing while clarifying; only block Enter-submit when streaming generation
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submit()
    }
  }

  return (
    <div
      className={cn(
        'w-full',
        hero
          ? 'chat-composer-glass rounded-[28px] p-3 sm:p-4'
          : 'rounded-[22px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] p-2.5 shadow-[0_12px_36px_rgba(28,25,23,0.06)] dark:shadow-[0_12px_36px_rgba(0,0,0,0.35)]',
      )}
    >
      {contextChip && contextHref ? (
        <div className="mb-1 px-2">
          <Link
            to={contextHref}
            className="inline-flex items-center rounded-full bg-[var(--surface-1)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-0)] hover:text-[var(--brand)]"
          >
            {contextChip}
          </Link>
        </div>
      ) : null}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={hero ? 3 : 1}
        className={cn(
          'w-full resize-none bg-transparent px-2 py-2 text-[14px] leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] disabled:opacity-60',
          hero ? 'min-h-[84px]' : 'min-h-[44px]',
        )}
      />
      <div className="mt-1 flex items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-1">
          {onAttach ? (
            <AddAssetMenu
              variant="icon"
              label="Add"
              align="left"
              loading={isUploading}
              disabled={isStreaming}
              actions={[
                {
                  kind: 'context',
                  label: 'Add context',
                  accept: '.md,.txt,.markdown,text/plain,text/markdown',
                  hint: '.md or .txt brief for RAG',
                  onFiles: async (files) => {
                    const file = files[0]
                    if (file) await onAttach(file)
                  },
                },
              ]}
            />
          ) : null}
        </div>

        {isStreaming ? (
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--text-primary)] text-[var(--surface-2)] transition-opacity hover:opacity-90"
            title="Stop"
            onClick={() => void onStop?.()}
          >
            <Square className="h-3.5 w-3.5 fill-current" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void submit()}
            disabled={!value.trim() || disabled}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--brand-button)] text-white shadow-[0_8px_20px_rgba(230,25,77,0.35)] transition-opacity disabled:opacity-40"
            title="Send"
          >
            <ArrowUp className="h-4 w-4 stroke-[2.25]" />
          </button>
        )}
      </div>
    </div>
  )
}
