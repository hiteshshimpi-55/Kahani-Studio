import { useSystemHealth } from '@/features/system/hooks/use-system-health'
import { cn } from '@/lib/utils'

export function SystemStatusView() {
  const { health, error, jobId, busy, loadHealth, enqueuePing } = useSystemHealth()

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8 px-6 py-12">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">Base stack</h1>
        <p className="text-stone-600">
          Vite frontend, FastAPI API, Redis queue, Postgres, and ARQ worker — no
          product features yet.
        </p>
      </header>

      <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium">System health</h2>
          <button
            type="button"
            onClick={() => void loadHealth()}
            className={cn(
              'rounded border border-stone-400 px-3 py-1.5 text-sm text-stone-800',
              'hover:bg-stone-200',
            )}
          >
            Refresh
          </button>
        </div>

        {error ? <p className="text-sm text-red-700">{error}</p> : null}

        {health ? (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-stone-500">API</dt>
              <dd className="font-medium">{health.status}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Service</dt>
              <dd className="font-medium">{health.service}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Postgres</dt>
              <dd className="font-medium">{health.postgres.ok ? 'ok' : 'down'}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Redis</dt>
              <dd className="font-medium">{health.redis.ok ? 'ok' : 'down'}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-stone-500">Data dir</dt>
              <dd className="font-mono text-xs">{health.data_dir}</dd>
            </div>
          </dl>
        ) : !error ? (
          <p className="text-sm text-stone-500">Loading…</p>
        ) : null}
      </section>

      <section className="rounded-lg border border-stone-300 bg-[#faf7f0] p-5">
        <h2 className="mb-3 text-lg font-medium">Worker queue</h2>
        <p className="mb-4 text-sm text-stone-600">
          Enqueues a smoke-test job. The worker writes to{' '}
          <code className="rounded bg-stone-200 px-1">/data/worker_ping.txt</code>.
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={() => void enqueuePing()}
          className="rounded bg-stone-900 px-4 py-2 text-sm text-stone-50 disabled:opacity-50"
        >
          {busy ? 'Enqueueing…' : 'Enqueue ping job'}
        </button>
        {jobId ? (
          <p className="mt-3 font-mono text-xs text-stone-600">job_id: {jobId}</p>
        ) : null}
      </section>
    </div>
  )
}
