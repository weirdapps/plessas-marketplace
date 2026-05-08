import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const resolveMriTool: Tool = {
  name: 'teams_resolve_mri',
  description: 'Resolve a Teams MRI (8:orgid:<aad-oid>) to {id, email, displayName} via Graph /users/{id}.',
  inputSchema: {
    type: 'object',
    properties: {
      mri: { type: 'string', description: 'Teams MRI string to resolve.' },
    },
    required: ['mri'],
    additionalProperties: false,
  },
  handler: async (args) => runTeamsCli(['resolve-mri', args.mri]),
};
