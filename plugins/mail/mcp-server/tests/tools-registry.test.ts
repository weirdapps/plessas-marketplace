// tests/tools-registry.test.ts
import { describe, it, expect } from 'vitest';
import {
  authCheckTool, listMailTool, getMailTool, downloadAttachmentsTool,
  listCalendarTool, getEventTool, listFoldersTool, findFolderTool,
  createFolderTool, moveMailTool,
  // v0.2.0 — write-side tools
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
} from '../src/tools/index.js';

const READ_TOOLS = [
  authCheckTool, listMailTool, getMailTool, downloadAttachmentsTool,
  listCalendarTool, getEventTool, listFoldersTool, findFolderTool,
  createFolderTool, moveMailTool,
];

const WRITE_TOOLS = [
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
];

const ALL_TOOLS = [...READ_TOOLS, ...WRITE_TOOLS];

describe('tool registry', () => {
  it('has 15 unique tool names (10 read + 5 write)', () => {
    const names = ALL_TOOLS.map(t => t.name);
    expect(new Set(names).size).toBe(15);
  });
  it('every tool has description and inputSchema', () => {
    for (const t of ALL_TOOLS) {
      expect(t.description.length).toBeGreaterThan(20);
      expect(t.inputSchema).toMatchObject({ type: 'object' });
    }
  });
  it('every tool name uses outlook_ prefix', () => {
    for (const t of ALL_TOOLS) {
      expect(t.name).toMatch(/^outlook_/);
    }
  });
});

describe('v0.2.0 write-side tools', () => {
  it('outlook_send_mail requires to + subject', () => {
    const schema = sendMailTool.inputSchema as { required: string[] };
    expect(schema.required).toContain('to');
    expect(schema.required).toContain('subject');
  });

  it('outlook_reply / outlook_reply_all share the same schema', () => {
    expect(replyTool.inputSchema).toEqual(replyAllTool.inputSchema);
  });

  it('outlook_reply requires message_id', () => {
    const schema = replyTool.inputSchema as { required: string[] };
    expect(schema.required).toContain('message_id');
  });

  it('outlook_forward requires message_id AND to', () => {
    const schema = forwardTool.inputSchema as { required: string[] };
    expect(schema.required).toContain('message_id');
    expect(schema.required).toContain('to');
  });

  it('outlook_capture_signature has no required args (sensible defaults)', () => {
    const schema = captureSignatureTool.inputSchema as { required?: string[] };
    expect(schema.required).toBeUndefined();
  });
});
