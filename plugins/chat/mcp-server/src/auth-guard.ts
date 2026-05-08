import { runTeamsCli, TeamsCliError } from './subprocess.js';

export interface AuthCheckResult {
  status: 'ok' | 'expired' | 'missing';
  tokenExpiresAt?: string;
  account?: { upn: string; displayName?: string };
  hoursRemaining?: number;
}

export async function checkAuth(): Promise<AuthCheckResult> {
  try {
    const raw = await runTeamsCli<{
      status: string;
      tokenExpiresAt?: string;
      account?: { upn: string; displayName?: string };
    }>(['auth-check']);
    if (raw.status !== 'ok') return { status: 'expired' };
    const expires = raw.tokenExpiresAt ? new Date(raw.tokenExpiresAt).getTime() : 0;
    const hoursRemaining = expires > 0 ? Math.floor((expires - Date.now()) / 3_600_000) : 0;
    return {
      status: 'ok',
      tokenExpiresAt: raw.tokenExpiresAt,
      account: raw.account,
      hoursRemaining,
    };
  } catch (err) {
    if (err instanceof TeamsCliError && err.code === 'auth_required') {
      return { status: 'missing' };
    }
    throw err;
  }
}
