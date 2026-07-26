import type { McpToolCatalogItem } from '../types'
import { cn } from '@/lib/utils'

type Props = {
  tools: McpToolCatalogItem[]
  className?: string
}

export function McpToolsList({ tools, className }: Props) {
  return (
    <section className={cn('mcp-enter-delayed space-y-3', className)}>
      <div>
        <h2 className="text-[16px] font-semibold tracking-tight text-[var(--text-primary)]">
          Tools
        </h2>
        <p className="mt-0.5 text-[13px] text-[var(--text-secondary)]">
          What agents can call — output is an episode audio URL, not raw bytes.
        </p>
      </div>
      <ul className="space-y-2.5">
        {tools.map((tool) => (
          <li
            key={tool.name}
            className="group rounded-[12px] border border-[var(--folio-border)] bg-[var(--surface-2)] px-4 py-3.5 transition-colors hover:border-[var(--brand)]/35"
          >
            <p className="font-mono text-[13px] font-semibold text-[var(--brand)]">{tool.name}</p>
            <p className="mt-1 text-[13px] leading-5 text-[var(--text-secondary)]">
              {tool.description}
            </p>
            {tool.arguments?.length ? (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {tool.arguments.map((arg) => (
                  <span
                    key={arg.name}
                    title={arg.description}
                    className="inline-flex items-center gap-1 rounded-[6px] border border-[var(--folio-border)] bg-[var(--surface-0)] px-2 py-0.5 font-mono text-[11px] text-[var(--text-primary)]"
                  >
                    {arg.name}
                    <span className="text-[var(--text-secondary)]">{arg.type}</span>
                    {arg.required ? (
                      <span className="text-[var(--brand)]">*</span>
                    ) : null}
                  </span>
                ))}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
