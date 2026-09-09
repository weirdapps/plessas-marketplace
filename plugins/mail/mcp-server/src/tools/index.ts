// src/tools/index.ts — barrel re-export for the 16 outlook-bridge tools
// (10 read-side from v0.1.0 + 5 write-side from v0.2.0 + 1 diagnostic from v0.4.0)
// and ALL_TOOLS, the one registry both server.ts and the tests read.
import { authCheckTool } from './auth-check.js';
import { listMailTool } from './list-mail.js';
import { getMailTool } from './get-mail.js';
import { downloadAttachmentsTool } from './download-attachments.js';
import { listCalendarTool } from './list-calendar.js';
import { getEventTool } from './get-event.js';
import { listFoldersTool } from './list-folders.js';
import { findFolderTool } from './find-folder.js';
import { createFolderTool } from './create-folder.js';
import { moveMailTool } from './move-mail.js';
// v0.2.0 — write side (outlook-cli v1.3.0 send-mail + v1.4.0 reply/forward).
import { sendMailTool } from './send-mail.js';
import { replyTool, replyAllTool } from './reply.js';
import { forwardTool } from './forward.js';
import { captureSignatureTool } from './capture-signature.js';
// v0.4.0: diagnostics.
import { doctorTool } from './doctor.js';

export {
  authCheckTool, listMailTool, getMailTool, downloadAttachmentsTool,
  listCalendarTool, getEventTool, listFoldersTool, findFolderTool,
  createFolderTool, moveMailTool,
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
  doctorTool,
};

/** The registry the MCP server serves. Single source of truth for the tool list. */
export const ALL_TOOLS = [
  // Read-side (v0.1.0)
  authCheckTool, listMailTool, getMailTool, downloadAttachmentsTool,
  listCalendarTool, getEventTool, listFoldersTool, findFolderTool,
  createFolderTool, moveMailTool,
  // Write-side (v0.2.0)
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
  // Diagnostics (v0.4.0)
  doctorTool,
];
