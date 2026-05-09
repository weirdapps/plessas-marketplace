// src/server.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

import { authCheckTool } from './tools/auth-check.js';
import { listMailTool } from './tools/list-mail.js';
import { getMailTool } from './tools/get-mail.js';
import { downloadAttachmentsTool } from './tools/download-attachments.js';
import { listCalendarTool } from './tools/list-calendar.js';
import { getEventTool } from './tools/get-event.js';
import { listFoldersTool } from './tools/list-folders.js';
import { findFolderTool } from './tools/find-folder.js';
import { createFolderTool } from './tools/create-folder.js';
import { moveMailTool } from './tools/move-mail.js';
// v0.2.0 — write-side tools.
import { sendMailTool } from './tools/send-mail.js';
import { replyTool, replyAllTool } from './tools/reply.js';
import { forwardTool } from './tools/forward.js';
import { captureSignatureTool } from './tools/capture-signature.js';
import { doctorTool } from './tools/doctor.js';
import { OutlookCliError } from './subprocess.js';

const TOOLS = [
  // Read-side (v0.1.0)
  authCheckTool, listMailTool, getMailTool, downloadAttachmentsTool,
  listCalendarTool, getEventTool, listFoldersTool, findFolderTool,
  createFolderTool, moveMailTool,
  // Write-side (v0.2.0)
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
  // Diagnostics (v0.4.0)
  doctorTool,
];
const TOOLS_BY_NAME = Object.fromEntries(TOOLS.map(t => [t.name, t]));

const server = new Server(
  { name: 'outlook-bridge', version: '0.4.0' },
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
    if (err instanceof OutlookCliError) {
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
