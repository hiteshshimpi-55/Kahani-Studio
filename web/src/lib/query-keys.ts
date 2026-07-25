export const queryKeys = {
  system: {
    health: ['system', 'health'] as const,
  },
  projects: {
    all: ['projects'] as const,
    detail: (id: string) => ['projects', id] as const,
    attachments: (id: string) => ['projects', id, 'attachments'] as const,
    run: (projectId: string, runId: string) =>
      ['projects', projectId, 'runs', runId] as const,
    scriptLatest: (id: string) => ['projects', id, 'scripts', 'latest'] as const,
  },
}
