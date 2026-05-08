// src/tools/index.ts — barrel re-export for the 15 outlook-bridge tools
// (10 read-side from v0.1.0 + 5 write-side from v0.2.0).
export { authCheckTool } from './auth-check.js';
export { listMailTool } from './list-mail.js';
export { getMailTool } from './get-mail.js';
export { downloadAttachmentsTool } from './download-attachments.js';
export { listCalendarTool } from './list-calendar.js';
export { getEventTool } from './get-event.js';
export { listFoldersTool } from './list-folders.js';
export { findFolderTool } from './find-folder.js';
export { createFolderTool } from './create-folder.js';
export { moveMailTool } from './move-mail.js';
// v0.2.0 — write side (outlook-cli v1.3.0 send-mail + v1.4.0 reply/forward).
export { sendMailTool } from './send-mail.js';
export { replyTool, replyAllTool } from './reply.js';
export { forwardTool } from './forward.js';
export { captureSignatureTool } from './capture-signature.js';
