// tests/validate-args.test.ts
import { describe, it, expect } from 'vitest';
import { validateArgs } from '../src/validate-args.js';
import { ALL_TOOLS, sendMailTool, getMailTool, moveMailTool, listMailTool } from '../src/tools/index.js';
import type { Tool } from '../src/tool.js';

describe('validateArgs', () => {
  it('names the missing required field instead of failing opaquely later', () => {
    expect(validateArgs(sendMailTool, { subject: 's' }))
      .toBe('missing required argument: to');
    expect(validateArgs(getMailTool, {}))
      .toBe('missing required argument: id');
  });

  it('treats an explicit null as missing', () => {
    expect(validateArgs(getMailTool, { id: null })).toBe('missing required argument: id');
  });

  it('accepts arguments that satisfy the schema', () => {
    expect(validateArgs(getMailTool, { id: 'AAMk-1', body: 'text' })).toBeNull();
    expect(validateArgs(moveMailTool, { ids: ['a'], to: 'Archive', continueOnError: true })).toBeNull();
    expect(validateArgs(listMailTool, { folder: 'Inbox', top: 5, all: false })).toBeNull();
  });

  it('rejects a declared type mismatch and names the field', () => {
    expect(validateArgs(getMailTool, { id: 42 }))
      .toBe("argument 'id' must be string, got number");
    expect(validateArgs(moveMailTool, { ids: 'not-an-array', to: 'Archive' }))
      .toBe("argument 'ids' must be array, got string");
    expect(validateArgs(listMailTool, { all: 'yes' }))
      .toBe("argument 'all' must be boolean, got string");
  });

  it('distinguishes integer from number', () => {
    expect(validateArgs(listMailTool, { top: 3 })).toBeNull();
    expect(validateArgs(listMailTool, { top: 3.5 }))
      .toBe("argument 'top' must be integer, got number");
  });

  it('rejects a value outside a declared enum', () => {
    expect(validateArgs(getMailTool, { id: 'x', body: 'markdown' }))
      .toBe('argument \'body\' must be one of: html, text, none');
  });

  it('enforces the declared batch cap, which nothing checked before', () => {
    // outlook_move_mail advertises maxItems 20. Neither this server nor the CLI
    // (which validates only "at least one id") enforced it, so the documented
    // cap was a suggestion.
    const twentyOne = Array.from({ length: 21 }, (_, i) => `id-${i}`);
    expect(validateArgs(moveMailTool, { ids: twentyOne, to: 'Archive' }))
      .toBe("argument 'ids' takes at most 20 item(s), got 21");
    const twenty = Array.from({ length: 20 }, (_, i) => `id-${i}`);
    expect(validateArgs(moveMailTool, { ids: twenty, to: 'Archive' })).toBeNull();
  });

  it('enforces the declared minimum item count', () => {
    expect(validateArgs(moveMailTool, { ids: [], to: 'Archive' }))
      .toBe("argument 'ids' needs at least 1 item(s), got 0");
  });

  it('enforces declared numeric bounds', () => {
    expect(validateArgs(listMailTool, { top: 101 }))
      .toBe("argument 'top' must be <= 100, got 101");
    expect(validateArgs(listMailTool, { top: 0 }))
      .toBe("argument 'top' must be >= 1, got 0");
    expect(validateArgs(listMailTool, { top: 100 })).toBeNull();
  });

  it('ignores undeclared keys rather than guessing', () => {
    expect(validateArgs(getMailTool, { id: 'x', speculative: true })).toBeNull();
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
