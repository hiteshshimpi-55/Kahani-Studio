import { Button } from '@/components/ui/button'
import { useSystemHealth } from '@/features/system/hooks/use-system-health'

export function SystemStatusView() {
  const { health, error, jobId, busy, loadHealth, enqueuePing } = useSystemHealth()

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">System</h1>
        <p className="text-muted-foreground">
          Health checks for API, Postgres, Redis, and the ARQ worker queue.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium">System health</h2>
          <Button type="button" variant="secondary" size="sm" onClick={() => void loadHealth()}>
            Refresh
          </Button>
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        {health ? (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">API</dt>
              <dd className="font-medium">{health.status}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Service</dt>
              <dd className="font-medium">{health.service}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Postgres</dt>
              <dd className="font-medium">{health.postgres.ok ? 'ok' : 'down'}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Redis</dt>
              <dd className="font-medium">{health.redis.ok ? 'ok' : 'down'}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-muted-foreground">Data dir</dt>
              <dd className="font-mono text-xs">{health.data_dir}</dd>
            </div>
          </dl>
        ) : !error ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : null}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h2 className="mb-3 text-lg font-medium">Worker queue</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Enqueues a smoke-test job. The worker writes to{' '}
          <code className="rounded bg-muted px-1">/data/worker_ping.txt</code>.
        </p>
        <Button type="button" disabled={busy} onClick={() => void enqueuePing()}>
          {busy ? 'Enqueueing…' : 'Enqueue ping job'}
        </Button>
        {jobId ? (
          <p className="mt-3 font-mono text-xs text-muted-foreground">job_id: {jobId}</p>
        ) : null}
      </section>
    </div>
  )
}
