// Central place for runtime configuration. All values come from Vite env
// variables (see .env.example) so the backend can be re-pointed without code changes.

function toNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const env = import.meta.env;

export const config = {
  useMockByDefault: String(env.VITE_USE_MOCK ?? 'false').toLowerCase() !== 'false',
  apiBaseUrl: (env.VITE_API_BASE_URL || '').replace(/\/+$/, ''),
  requestTimeoutMs: toNumber(env.VITE_API_TIMEOUT_MS, 600000),
  pollIntervalMs: toNumber(env.VITE_API_POLL_INTERVAL_MS, 1000),
  maxFileMb: toNumber(env.VITE_MAX_FILE_MB, 25),
};

export const apiUrl = (path) => `${config.apiBaseUrl}${path}`;
