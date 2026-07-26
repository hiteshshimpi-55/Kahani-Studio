export const env = {
  /** Backend origin for API calls, e.g. http://localhost:8000. Empty = same origin. */
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
  /** Optional override for the Kahani MCP Streamable HTTP URL. */
  mcpUrl: (import.meta.env.VITE_MCP_URL ?? '').replace(/\/$/, ''),
} as const
