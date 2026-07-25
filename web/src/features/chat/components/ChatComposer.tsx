import { ArrowUp, LoaderCircle, Paperclip, Square } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'

import { cn } from '@/lib/utils'

type Props = {
  onSend: (text: string) => void | Promise<void>
  onAttach?: (file: File) => void | Promise<void>
  isStreaming?: boolean
  isUploading?: boolean
  disabled?: boolean
  variant?: 'default' | 'hero'
  placeholder?: string
}

export function ChatComposer({
  onSend,
  onAttach,
  isStreaming = false,
  isUploading = false,
  disabled = false,
  variant = 'default',
  placeholder = 'Describe the story you want to generate…',
}: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
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
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        disabled={disabled || isStreaming}
        rows={hero ? 3 : 1}
        className={cn(
          'w-full resize-none bg-transparent px-2 py-2 text-[14px] leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] disabled:opacity-60',
          hero ? 'min-h-[84px]' : 'min-h-[44px]',
        )}
      />
      <div className="mt-1 flex items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-1">
          <input
            ref={fileRef}
            type="file"
            className="sr-only"
            accept=".md,.txt,.markdown,text/plain,text/markdown"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file && onAttach) void onAttach(file)
              e.target.value = ''
            }}
          />
          <button
            type="button"
            title="Attach context file"
            disabled={!onAttach || isUploading || isStreaming}
            onClick={() => fileRef.current?.click()}
            className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)] disabled:opacity-40"
          >
            {isUploading ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Paperclip className="h-4 w-4 stroke-[1.75]" />
            )}
          </button>
        </div>

        {isStreaming ? (
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--text-primary)] text-[var(--surface-2)]"
            title="Generating…"
            disabled
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
