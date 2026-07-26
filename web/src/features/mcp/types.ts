export type McpToolArg = {
  name: string
  type: string
  required?: boolean
  description?: string
}

export type McpToolCatalogItem = {
  name: string
  description: string
  arguments: McpToolArg[]
}

export type McpToolsCatalog = {
  mcp_url: string
  tools: McpToolCatalogItem[]
}
