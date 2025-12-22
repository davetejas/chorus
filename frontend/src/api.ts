export type TokenResponse = {
  url: string;
  room: string;
  identity: string;
  token: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export async function fetchToken(room: string, name: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/api/token`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ room, name, kind: 'standard' }),
  });

  if (!res.ok) {
    throw new Error(`Token request failed: ${res.status} ${await res.text()}`);
  }

  return res.json();
}
