import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const authRenewTool: Tool = {
  name: 'teams_auth_renew',
  description: 'Silently renew the Teams Bearer using the persisted browser profile (headless).',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  // Derived, not rounded: teams-access/src/commands/auth-renew.ts:24 allows 90s
  // for the headless renewal and :32 keeps the browser open a further 40s so the
  // slower audiences land, so a healthy renewal runs to 130s. Plus the 15s
  // process-startup allowance used across this server = 145s. The old 60s
  // default SIGTERMed it at less than half its budget and reported
  // {error:'internal'}. Do not shrink the settle window instead: doing so caused
  // a multi-day "graph audience missing" outage, per the comment upstream.
  handler: async () => runTeamsCli(['auth-renew'], { timeoutMs: 145_000, idempotent: false }),
};
