import { cn } from '@/lib/utils'

type Props = {
  text: string
  active?: boolean
  className?: string
}

export function StreamingText({ text, active, className }: Props) {
  return (
    <p className={cn('whitespace-pre-wrap', className)}>
      {text}
      {active ? <span className="chat-stream-cursor" aria-hidden /> : null}
    </p>
  )
}
