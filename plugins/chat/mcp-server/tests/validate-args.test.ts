// tests/validate-args.test.ts
import { describe, it, expect } from 'vitest';
import { validateArgs } from '../src/validate-args.js';
import { ALL_TOOLS, sendMessageTool, resolveMriTool, listMessagesTool, listChatsTool } from '../src/tools/index.js';
import type { Tool } from '../src/tool.js';

describe('validateArgs', () => {
  it('names the missing required field instead of failing opaquely later', () => {
    expect(validateArgs(sendMessageTool, { body: 'hi' }))
      .toBe('missing required argument: chat_id');
    expect(validateArgs(sendMessageTool, { chat_id: '19:x@thread.v2' }))
      .toBe('missing required argument: body');
    expect(validateArgs(resolveMriTool, {}))
      .toBe('missing required argument: mri');
  });

  it('treats an explicit null as missing', () => {
    expect(validateArgs(resolveMriTool, { mri: null })).toBe('missing required argument: mri');
  });

  it('accepts arguments that satisfy the schema', () => {
    expect(validateArgs(sendMessageTool, { chat_id: '19:x@thread.v2', body: 'hi' })).toBeNull();
    expect(validateArgs(sendMessageTool, { chat_id: '19:x@thread.v2', body: 'hi', format: 'html' })).toBeNull();
    expect(validateArgs(listMessagesTool, { chat_id: '19:x@thread.v2', top: 20 })).toBeNull();
  });

  it('rejects a declared type mismatch and names the field', () => {
    expect(validateArgs(sendMessageTool, { chat_id: 19, body: 'hi' }))
      .toBe("argument 'chat_id' must be string, got number");
    expect(validateArgs(sendMessageTool, { chat_id: '19:x', body: ['a', 'b'] }))
      .toBe("argument 'body' must be string, got array");
  });

  it('distinguishes integer from number', () => {
    expect(validateArgs(listChatsTool, { top: 10 })).toBeNull();
    expect(validateArgs(listChatsTool, { top: 10.5 }))
      .toBe("argument 'top' must be integer, got number");
  });

  it('rejects a value outside a declared enum', () => {
    expect(validateArgs(sendMessageTool, { chat_id: '19:x', body: 'hi', format: 'markdown' }))
      .toBe('argument \'format\' must be one of: html, text');
  });

  it('enforces declared numeric bounds', () => {
    expect(validateArgs(listChatsTool, { top: 101 }))
      .toBe("argument 'top' must be <= 100, got 101");
    expect(validateArgs(listChatsTool, { top: 0 }))
      .toBe("argument 'top' must be >= 1, got 0");
    expect(validateArgs(listChatsTool, { top: 100 })).toBeNull();
  });

  it('ignores undeclared keys rather than guessing', () => {
    expect(validateArgs(resolveMriTool, { mri: '8:orgid:abc', speculative: true })).toBeNull();
  });

  it('passes every tool that is called with no arguments and requires none', () => {
    let checked = 0;
    for (const tool of ALL_TOOLS) {
      const schema = tool.inputSchema as { required?: string[] };
      if (schema.required?.length) continue;
      expect(validateArgs(tool, {})).toBeNull();
      checked++;
    }
    // Without this the test passes vacuously the day every tool gains a
    // required field, or the barrel stops exporting.
    expect(checked).toBeGreaterThan(0);
  });

  it('does not judge a type it does not model', () => {
    const exotic = {
      name: 'x', description: 'y', handler: async () => ({}),
      inputSchema: { type: 'object', properties: { weird: { type: 'null' } } },
    } as Tool;
    expect(validateArgs(exotic, { weird: 'anything' })).toBeNull();
  });
});
