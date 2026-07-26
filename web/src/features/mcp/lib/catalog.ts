import type { McpToolCatalogItem } from '../types'

/** Fallback catalog if the API is unreachable — keep in sync with backend catalog. */
export const FALLBACK_TOOLS: McpToolCatalogItem[] = [
  {
    name: 'kahani_render_episode',
    description:
      'Start a Kahani headless production job: script + narration mix for a short serial episode. Returns a job_id immediately — poll kahani_get_render until done.',
    arguments: [
      {
        name: 'prompt',
        type: 'string',
        required: true,
        description: 'Story brief or episode prompt',
      },
      {
        name: 'language',
        type: 'string',
        required: false,
        description: 'hi or en (default hi)',
      },
      {
        name: 'title',
        type: 'string',
        required: false,
        description: 'Optional episode title',
      },
    ],
  },
  {
    name: 'kahani_get_render',
    description:
      'Poll a render job. When status is done, returns audio_url plus metadata (never raw audio bytes).',
    arguments: [
      {
        name: 'job_id',
        type: 'string',
        required: true,
        description: 'Job id from kahani_render_episode',
      },
    ],
  },
  {
    name: 'kahani_discover_hooks',
    description:
      'Research a topic and return ranked story hooks / plot pitch cards for Pocket FM–style serials.',
    arguments: [
      {
        name: 'topic',
        type: 'string',
        required: true,
        description: 'Topic, trend, or news hook to explore',
      },
    ],
  },
]

export type InstallClient = 'cursor' | 'claude-code' | 'claude-desktop'

export function installSnippet(client: InstallClient, mcpUrl: string): string {
  switch (client) {
    case 'cursor':
      return JSON.stringify(
        {
          mcpServers: {
            kahani: {
              url: mcpUrl,
            },
          },
        },
        null,
        2,
      )
    case 'claude-code':
      return `# Add Kahani MCP (Streamable HTTP)
claude mcp add --transport http kahani ${mcpUrl}

# Or set in ~/.claude.json under mcpServers:
# "kahani": { "type": "http", "url": "${mcpUrl}" }`
    case 'claude-desktop':
      return JSON.stringify(
        {
          mcpServers: {
            kahani: {
              url: mcpUrl,
            },
          },
        },
        null,
        2,
      )
  }
}

export function installSteps(client: InstallClient): string[] {
  switch (client) {
    case 'cursor':
      return [
        'Open Cursor Settings → MCP (or edit ~/.cursor/mcp.json).',
        'Paste the JSON snippet and save.',
        'Reload MCP servers, then ask the agent to call kahani_render_episode.',
      ]
    case 'claude-code':
      return [
        'Run the CLI command below (or merge the JSON into your Claude Code MCP config).',
        'Restart the session so Kahani tools appear.',
        'Ask Claude to render an episode from a story brief.',
      ]
    case 'claude-desktop':
      return [
        'Edit claude_desktop_config.json (Claude → Settings → Developer).',
        'Merge the kahani server entry and restart Claude Desktop.',
        'Confirm Kahani tools are listed, then try a render.',
      ]
  }
}
