const LIVEKIT_API_KEY = import.meta.env.VITE_LIVEKIT_API_KEY ?? 'devkey';
const LIVEKIT_API_SECRET = import.meta.env.VITE_LIVEKIT_API_SECRET ?? 'devsecret';
const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL ?? 'ws://localhost:7880';

function base64url(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let str = '';
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export async function generateToken(
  room: string,
  identity: string,
  name: string,
): Promise<{ token: string; url: string }> {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    iss: LIVEKIT_API_KEY,
    sub: identity,
    name,
    nbf: now,
    exp: now + 7200,
    video: {
      roomJoin: true,
      room,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    },
  };

  const enc = new TextEncoder();
  const headerB64 = base64url(enc.encode(JSON.stringify(header)));
  const payloadB64 = base64url(enc.encode(JSON.stringify(payload)));
  const sigInput = `${headerB64}.${payloadB64}`;

  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(LIVEKIT_API_SECRET),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(sigInput));

  return { token: `${sigInput}.${base64url(sig)}`, url: LIVEKIT_URL };
}
