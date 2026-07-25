export type HealthDependency = {
  ok: boolean
  error: string | null
}

export type HealthResponse = {
  status: string
  service: string
  postgres: HealthDependency
  redis: HealthDependency
  data_dir: string
}

export type EnqueuePingResponse = {
  job_id: string | null
  queued: boolean
}
