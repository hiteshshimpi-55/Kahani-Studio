import { BrandMark } from '@/components/brand/BrandMark'
import { cn } from '@/lib/utils'

import { CopyButton } from './CopyButton'

type Props = {
  mcpUrl: string
  live: boolean | null
  className?: string
}

export function McpConnectionCard({ mcpUrl, live, className }: Props) {
  return (
    <section
      className={cn(
        'mcp-enter relative overflow-hidden rounded-[16px] border border-[var(--folio-border-strong)] bg-[var(--surface-2)] p-5 shadow-[var(--shadow-card)] md:p-6',
        className,
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.55]"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 12% 20%, color-mix(in srgb, var(--brand) 14%, transparent), transparent 55%), radial-gradient(ellipse 50% 40% at 90% 80%, color-mix(in srgb, var(--brand) 8%, transparent), transparent 60%)',
        }}
      />
      <svg
        aria-hidden
        className="pointer-events-none absolute right-4 bottom-3 h-16 w-[220px] text-[var(--brand)] opacity-[0.18] md:h-20 md:w-[280px]"
        viewBox="0 0 280 64"
        fill="none"
      >
        <path
          d="M0 32 C20 12, 40 52, 60 32 S100 12, 120 32 S160 52, 180 32 S220 12, 240 32 S260 52, 280 32"
          stroke="currentColor"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
      </svg>

      <div className="relative flex flex-col gap-5">
        <div className="flex flex-wrap items-center gap-3">
          <BrandMark size={56} className="rounded-[12px] shadow-[0_4px_16px_rgba(230,25,77,0.12)]" />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-[18px] font-semibold tracking-tight text-[var(--text-primary)]">
                Connection
              </h2>
              <span
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold tracking-wide uppercase',
                  live === true && 'bg-[var(--brand)]/10 text-[var(--brand)]',
                  live === false && 'bg-[var(--surface-1)] text-[var(--text-secondary)]',
                  live === null && 'bg-[var(--surface-1)] text-[var(--text-secondary)]',
                )}
              >
                <span
                  className={cn(
                    'h-1.5 w-1.5 rounded-full',
                    live === true && 'bg-[var(--brand)]',
                    live !== true && 'bg-[var(--text-secondary)]',
                  )}
                />
                {live === true ? 'Live' : live === false ? 'Offline' : 'Checking'}
              </span>
            </div>
            <p className="mt-0.5 text-[13px] text-[var(--text-secondary)]">
              Streamable HTTP endpoint for Cursor, Claude Code, and Claude Desktop
            </p>
          </div>
        </div>

        <div>
          <p className="mb-1.5 text-[11px] font-semibold tracking-[0.12em] text-[var(--text-secondary)] uppercase">
            Server URL
          </p>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <code className="min-w-0 flex-1 truncate rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-3 py-2.5 font-mono text-[13px] text-[var(--text-primary)]">
              {mcpUrl}
            </code>
            <CopyButton value={mcpUrl} className="shrink-0" />
          </div>
        </div>
      </div>
    </section>
  )
}
