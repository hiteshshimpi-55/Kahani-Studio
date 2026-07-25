import { Button } from '@/components/ui/button'
import { useSystemHealth } from '@/features/system/hooks/use-system-health'

export function SystemStatusView() {
  const { health, error, jobId, busy, loadHealth, enqueuePing } = useSystemHealth()

  return (
    <div className="mx-auto max-w-2xl">
      <header className="flex flex-col gap-1">
        <h1 className="text-[22px] font-semibold tracking-tight text-[var(--text-primary)]">
          System
        </h1>
        <p className="text-[13px] text-[var(--text-secondary)]">
          Health checks for API, Postgres, Redis, and the ARQ worker queue.
        </p>
      </header>

      <section className="mt-6 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-[14px] font-semibold text-[var(--text-primary)]">System health</h2>
          <Button type="button" variant="secondary" size="sm" onClick={() => void loadHealth()}>
            Refresh
          </Button>
        </div>

        {error ? <p className="text-[13px] text-destructive">{error}</p> : null}

        {health ? (
          <dl className="grid grid-cols-2 gap-3 text-[13px]">
            <div>
              <dt className="text-[11px] text-[var(--text-secondary)]">API</dt>
              <dd className="font-medium text-[var(--text-primary)]">{health.status}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-[var(--text-secondary)]">Service</dt>
              <dd className="font-medium text-[var(--text-primary)]">{health.service}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-[var(--text-secondary)]">Postgres</dt>
              <dd className="font-medium text-[var(--text-primary)]">
                {health.postgres.ok ? 'ok' : 'down'}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] text-[var(--text-secondary)]">Redis</dt>
              <dd className="font-medium text-[var(--text-primary)]">
                {health.redis.ok ? 'ok' : 'down'}
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="text-[11px] text-[var(--text-secondary)]">Data dir</dt>
              <dd className="font-mono text-[12px] text-[var(--text-primary)]">{health.data_dir}</dd>
            </div>
          </dl>
        ) : !error ? (
          <p className="text-[13px] text-[var(--text-secondary)]">Loading…</p>
        ) : null}
      </section>

      <section className="mt-4 rounded-[10px] border border-[var(--folio-border)] bg-[var(--surface-2)] p-5">
        <h2 className="mb-2 text-[14px] font-semibold text-[var(--text-primary)]">Worker queue</h2>
        <p className="mb-4 text-[13px] text-[var(--text-secondary)]">
          Enqueues a smoke-test job. The worker writes to{' '}
          <code className="rounded bg-[var(--surface-1)] px-1 text-[12px]">/data/worker_ping.txt</code>
          .
        </p>
        <Button type="button" disabled={busy} onClick={() => void enqueuePing()}>
          {busy ? 'Enqueueing…' : 'Enqueue ping job'}
        </Button>
        {jobId ? (
          <p className="mt-3 font-mono text-[11px] text-[var(--text-secondary)]">job_id: {jobId}</p>
        ) : null}
      </section>
    </div>
  )
}
