import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

// ALL_TOOLS is the single registry: adding a tool to the barrel serves it here
// and covers it in tests/tools-registry.test.ts at the same time.
import { ALL_TOOLS } from './tools/index.js';
import { TeamsCliError } from './subprocess.js';
import { validateArgs } from './validate-args.js';
import pkg from '../package.json' with { type: 'json' };

const TOOLS_BY_NAME = Object.fromEntries(ALL_TOOLS.map(t => [t.name, t]));

const server = new Server(
  { name: 'teams-bridge', version: pkg.version },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: ALL_TOOLS.map(t => ({ name: t.name, description: t.description, inputSchema: t.inputSchema })),
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const tool = TOOLS_BY_NAME[req.params.name];
  if (!tool) {
    return {
      content: [{ type: 'text', text: JSON.stringify({ error: 'unknown_tool', name: req.params.name }) }],
      isError: true,
    };
  }
  // Check against the declared inputSchema before spawning: an absent required
  // field otherwise reaches the CLI as `undefined` and comes back as an opaque
  // internal error instead of naming the field.
  const args = (req.params.arguments ?? {}) as Record<string, unknown>;
  const problem = validateArgs(tool, args);
  if (problem) {
    return {
      content: [{ type: 'text', text: JSON.stringify({
        error: 'invalid_input',
        message: problem,
        tool: req.params.name,
      }) }],
      isError: true,
    };
  }
  try {
    const result = await tool.handler(args);
    return { content: [{ type: 'text', text: JSON.stringify(result) }] };
  } catch (err) {
    if (err instanceof TeamsCliError) {
      return {
        content: [{ type: 'text', text: JSON.stringify({
          error: err.code,
          message: err.message,
          remediation: err.remediation,
          retryable: err.retryable,
        }) }],
        isError: true,
      };
    }
    return {
      content: [{ type: 'text', text: JSON.stringify({
        error: 'internal',
        message: (err as Error).message,
      }) }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
