// tests/doctor-root.test.ts
//
// The doctor anchors .last-startup.json and its "cd <dir> && npm ci" suggestion
// on the server root it derives from import.meta.url. That anchor used to be a
// fixed join(__dirname, '..', '..'), which is correct for exactly one of the two
// depths the server is started from, and the esbuild bundle is the other one.
import { describe, it, expect } from 'vitest';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findServerRoot } from '../src/tools/doctor.js';

const SERVER_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

describe('findServerRoot', () => {
  // dist/tools/ and bundle/ need not exist for this: the walk skips any level
  // with no readable package.json. What is being asserted is that both depths
  // land on the same directory, which the old fixed-depth join could not do.
  it.each([
    ['dist/tools/ (tsc output)', join(SERVER_ROOT, 'dist', 'tools')],
    ['bundle/ (esbuild output)', join(SERVER_ROOT, 'bundle')],
    ['the server root itself', SERVER_ROOT],
  ])('anchors on the server root from %s', (_label, start) => {
    expect(findServerRoot(start)).toBe(SERVER_ROOT);
  });

  // The control that makes the positives mean something: from a directory with
  // no teams-bridge-mcp ancestor the answer must be null, not the nearest
  // plausible directory. A wrong path is what produced the real "cd /private &&
  // npm install" suggestion when the bundle ran from a temp dir.
  it('returns null instead of a wrong path when the root is not an ancestor', () => {
    expect(findServerRoot(mkdtempSync(join(tmpdir(), 'mcp-root-')))).toBeNull();
  });
});
