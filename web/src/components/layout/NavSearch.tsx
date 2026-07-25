import { Search } from 'lucide-react'

/** Dummy header search — visual parity with TCC NavSearch. */
export function NavSearch() {
  return (
    <div className="relative w-full max-w-[40rem]">
      <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-[var(--text-secondary)] opacity-70 stroke-[1.75]" />
      <input
        type="search"
        placeholder="Search projects…"
        disabled
        className="h-10 w-full cursor-default rounded-full bg-[var(--surface-1)] pr-3 pl-9 text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--folio-border-strong)] disabled:opacity-100"
      />
    </div>
  )
}
