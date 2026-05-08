import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

import { authCheckTool } from './tools/auth-check.js';
import { authRenewTool } from './tools/auth-renew.js';
import { healthCheckTool } from './tools/health-check.js';
import { listTeamsTool } from './tools/list-teams.js';
import { listChannelsTool } from './tools/list-channels.js';
import { listChatsTool } from './tools/list-chats.js';
import { listMessagesTool } from './tools/list-messages.js';
import { sendMessageTool } from './tools/send-message.js';
import { resolveMriTool } from './tools/resolve-mri.js';
import { loginTool } from './tools/login.js';
import { TeamsCliError } from './subprocess.js';

const TOOLS = [
  authCheckTool, authRenewTool, healthCheckTool, loginTool,
  listTeamsTool, listChannelsTool, listChatsTool, listMessagesTool,
  sendMessageTool, resolveMriTool,
];
const TOOLS_BY_NAME = Object.fromEntries(TOOLS.map(t => [t.name, t]));

const server = new Server(
  { name: 'teams-bridge', version: '0.1.0' },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS.map(t => ({ name: t.name, description: t.description, inputSchema: t.inputSchema })),
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const tool = TOOLS_BY_NAME[req.params.name];
  if (!tool) {
    return {
      content: [{ type: 'text', text: JSON.stringify({ error: 'unknown_tool', name: req.params.name }) }],
      isError: true,
    };
  }
  try {
    const result = await tool.handler(req.params.arguments ?? {});
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
