/**
 * Google OAuth configuration helper.
 *
 * Attempts to load the client ID from the following sources (in order):
 *   1. VITE_GOOGLE_CLIENT_ID environment variable.
 *   2. Any client_secret*.json file located in the project root (frontend/).
 */

type ClientSecret = {
  web?: {
    client_id?: string;
  };
  installed?: {
    client_id?: string;
  };
};

const envClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined) || '';

let resolvedClientId = envClientId;

if (!resolvedClientId) {
  const secretModules = import.meta.glob('../../client_secret*.json', {
    eager: true,
    import: 'default',
  }) as Record<string, ClientSecret>;

  for (const module of Object.values(secretModules)) {
    const candidate = module?.web?.client_id ?? module?.installed?.client_id;
    if (candidate) {
      resolvedClientId = candidate;
      break;
    }
  }
}

if (!resolvedClientId && import.meta.env.DEV) {
  console.warn(
    '[Google OAuth] No client ID found. Provide VITE_GOOGLE_CLIENT_ID or a client_secret JSON file in the frontend directory.',
  );
}

export const GOOGLE_CLIENT_ID = resolvedClientId;
export const isGoogleLoginConfigured = Boolean(GOOGLE_CLIENT_ID);
