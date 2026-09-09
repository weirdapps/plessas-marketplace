// src/validate-args.ts
//
// Minimal inputSchema check run at the dispatch point in server.ts. Without it a
// missing required field reaches spawn as `undefined` and the model gets an
// opaque internal error instead of the name of the field it forgot.
//
// Deliberately not a JSON-schema library: this covers `required` and the
// declared primitive types and enums, which is every constraint the tools in
// this server actually declare. Anything it cannot judge, it passes.
import type { Tool } from './tool.js';

interface PropertySpec {
  type?: string;
  enum?: unknown[];
  minItems?: number;
  maxItems?: number;
  minimum?: number;
  maximum?: number;
}

interface MinimalSchema {
  required?: string[];
  properties?: Record<string, PropertySpec>;
}

function matchesType(value: unknown, type: string): boolean {
  switch (type) {
    case 'string': return typeof value === 'string';
    case 'number': return typeof value === 'number' && Number.isFinite(value);
    case 'integer': return typeof value === 'number' && Number.isInteger(value);
    case 'boolean': return typeof value === 'boolean';
    case 'array': return Array.isArray(value);
    case 'object': return typeof value === 'object' && value !== null && !Array.isArray(value);
    default: return true; // unknown declared type: not ours to judge
  }
}

function describe(value: unknown): string {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}

/**
 * Returns a human-readable problem string, or null when the arguments are usable.
 * The message names the offending field, which is the entire point.
 */
export function validateArgs(tool: Tool, args: Record<string, unknown>): string | null {
  const schema = tool.inputSchema as MinimalSchema;

  for (const key of schema.required ?? []) {
    if (args[key] === undefined || args[key] === null) {
      return `missing required argument: ${key}`;
    }
  }

  for (const [key, value] of Object.entries(args)) {
    if (value === undefined || value === null) continue;
    const spec = schema.properties?.[key];
    if (!spec) continue; // undeclared key: additionalProperties is the CLI's problem
    if (spec.type && !matchesType(value, spec.type)) {
      return `argument '${key}' must be ${spec.type}, got ${describe(value)}`;
    }
    if (spec.enum && !spec.enum.includes(value)) {
      return `argument '${key}' must be one of: ${spec.enum.join(', ')}`;
    }
    // Bounds. Declared and previously unenforced: outlook_move_mail advertises a
    // 20-id cap that neither this server nor the CLI checked, so a 200-id batch
    // went straight through.
    if (Array.isArray(value)) {
      if (spec.minItems !== undefined && value.length < spec.minItems) {
        return `argument '${key}' needs at least ${spec.minItems} item(s), got ${value.length}`;
      }
      if (spec.maxItems !== undefined && value.length > spec.maxItems) {
        return `argument '${key}' takes at most ${spec.maxItems} item(s), got ${value.length}`;
      }
    }
    if (typeof value === 'number') {
      if (spec.minimum !== undefined && value < spec.minimum) {
        return `argument '${key}' must be >= ${spec.minimum}, got ${value}`;
      }
      if (spec.maximum !== undefined && value > spec.maximum) {
        return `argument '${key}' must be <= ${spec.maximum}, got ${value}`;
      }
    }
  }

  return null;
}
