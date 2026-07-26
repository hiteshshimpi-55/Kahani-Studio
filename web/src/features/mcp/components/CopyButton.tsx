import { Check, Copy } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type Props = {
  value: string
  className?: string
  label?: string
}

export function CopyButton({ value, className, label = 'Copy' }: Props) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const t = window.setTimeout(() => setCopied(false), 1600)
    return () => window.clearTimeout(t)
  }, [copied])

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
    } catch {
      /* ignore */
    }
  }

  return (
    <Button
      type="button"
      size="sm"
      variant={copied ? 'secondary' : 'primary'}
      onClick={onCopy}
      className={cn('gap-1.5', copied && 'mcp-copy-pulse', className)}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? 'Copied' : label}
    </Button>
  )
}
