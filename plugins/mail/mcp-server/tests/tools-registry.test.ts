// tests/tools-registry.test.ts
//
// Asserts against ALL_TOOLS, the same array src/server.ts serves, so a tool that
// is written but never registered fails here instead of shipping invisible.
import { describe, it, expect } from 'vitest';
import {
  ALL_TOOLS,
  // v0.2.0 — write-side tools
  sendMailTool, replyTool, replyAllTool, forwardTool, captureSignatureTool,
} from '../src/tools/index.js';

describe('tool registry', () => {
  it('has 16 unique tool names (10 read + 5 write + 1 diagnostic)', () => {
    const names = ALL_TOOLS.map(t => t.name);
    expect(names).toHaveLength(16);
    expect(new Set(names).size).toBe(16);
  });
  it('registers the diagnostics tool', () => {
    expect(ALL_TOOLS.map(t => t.name)).toContain('outlook_doctor');
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
