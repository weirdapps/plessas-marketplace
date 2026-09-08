import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const healthCheckTool: Tool = {
  name: 'teams_health_check',
  description: 'Probe Graph + chatsvc + chatsvcagg endpoints and report status for each.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  // The CLI writes the report and THEN exits non-zero to signal the verdict:
  // teams-access/src/cli.ts:213-214 exits 5 (Upstream) for 'broken' and 1
  // (Internal) for 'degraded'. Without these codes listed, the one tool whose
  // purpose is reporting bad states discarded its own report on every bad state.
  //
  // Timeout: 4 sequential probes at the CLI's 30s httpTimeoutMs default
  // (src/config/load.ts:17) is a 120s worst case, and a sick system is exactly
  // when probes run long. The old 30s could not outlast even one hung probe.
  handler: async () => runTeamsCli(['health-check'], {
    timeoutMs: 135_000,
    payloadExitCodes: [1, 5],
  }),
};
