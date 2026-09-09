// src/tools/index.ts: barrel re-export for the 11 teams-bridge tools, and
// ALL_TOOLS, the one registry both server.ts and the tests read.
import { authCheckTool } from './auth-check.js';
import { authRenewTool } from './auth-renew.js';
import { healthCheckTool } from './health-check.js';
import { loginTool } from './login.js';
import { listTeamsTool } from './list-teams.js';
import { listChannelsTool } from './list-channels.js';
import { listChatsTool } from './list-chats.js';
import { listMessagesTool } from './list-messages.js';
import { sendMessageTool } from './send-message.js';
import { resolveMriTool } from './resolve-mri.js';
import { doctorTool } from './doctor.js';

export {
  authCheckTool, authRenewTool, healthCheckTool, loginTool,
  listTeamsTool, listChannelsTool, listChatsTool, listMessagesTool,
  sendMessageTool, resolveMriTool,
  doctorTool,
};

/** The registry the MCP server serves. Single source of truth for the tool list. */
export const ALL_TOOLS = [
  authCheckTool, authRenewTool, healthCheckTool, loginTool,
  listTeamsTool, listChannelsTool, listChatsTool, listMessagesTool,
  sendMessageTool, resolveMriTool,
  // Diagnostics
  doctorTool,
];
