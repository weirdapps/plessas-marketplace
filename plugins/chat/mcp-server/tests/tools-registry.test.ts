// tests/tools-registry.test.ts
//
// Asserts against ALL_TOOLS, the same array src/server.ts serves, so a tool that
// is written but never registered fails here instead of shipping invisible.
import { describe, it, expect } from 'vitest';
import { ALL_TOOLS, sendMessageTool, listMessagesTool } from '../src/tools/index.js';

describe('tool registry', () => {
  it('has 11 unique tool names', () => {
    const names = ALL_TOOLS.map(t => t.name);
    expect(names).toHaveLength(11);
    expect(new Set(names).size).toBe(11);
  });
  it('registers the diagnostics tool', () => {
    expect(ALL_TOOLS.map(t => t.name)).toContain('teams_doctor');
  });
  it('every tool has description and inputSchema', () => {
    for (const t of ALL_TOOLS) {
      expect(t.description.length).toBeGreaterThan(20);
      expect(t.inputSchema).toMatchObject({ type: 'object' });
    }
  });
  it('every tool name uses teams_ prefix', () => {
    for (const t of ALL_TOOLS) {
      expect(t.name).toMatch(/^teams_/);
    }
  });
});

describe('tool schemas', () => {
  it('teams_send_message requires chat_id + body', () => {
    const schema = sendMessageTool.inputSchema as { required: string[] };
    expect(schema.required).toContain('chat_id');
    expect(schema.required).toContain('body');
  });

  it('teams_list_messages requires nothing (chat OR team+channel)', () => {
    const schema = listMessagesTool.inputSchema as { required?: string[] };
    expect(schema.required).toBeUndefined();
  });

  it('teams_list_messages advertises no since filter, because the CLI has none', () => {
    const schema = listMessagesTool.inputSchema as { properties: Record<string, unknown> };
    expect(schema.properties).not.toHaveProperty('since');
    expect(Object.keys(schema.properties)).toEqual(['chat_id', 'team_id', 'channel_id', 'top']);
  });
});
