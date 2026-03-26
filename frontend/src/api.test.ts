import { describe, it, expect } from 'vitest';
import { generateToken } from './api';

function decodeJwtPart(part: string): Record<string, unknown> {
  // Base64url → base64 → JSON
  const base64 = part.replace(/-/g, '+').replace(/_/g, '/');
  return JSON.parse(atob(base64));
}

describe('generateToken — happy path', () => {
  it('returns an object with token and url', async () => {
    const result = await generateToken('demo', 'alice', 'Alice');
    expect(typeof result.token).toBe('string');
    expect(typeof result.url).toBe('string');
  });

  it('token is a three-part dot-separated JWT', async () => {
    const { token } = await generateToken('demo', 'alice', 'Alice');
    const parts = token.split('.');
    expect(parts).toHaveLength(3);
    expect(parts.every((p) => p.length > 0)).toBe(true);
  });

  it('token header declares HS256', async () => {
    const { token } = await generateToken('demo', 'alice', 'Alice');
    const header = decodeJwtPart(token.split('.')[0]);
    expect(header).toEqual({ alg: 'HS256', typ: 'JWT' });
  });

  it('token payload contains correct identity and room claims', async () => {
    const now = Math.floor(Date.now() / 1000);
    const { token } = await generateToken('demo', 'alice', 'Alice');
    const payload = decodeJwtPart(token.split('.')[1]);

    expect(payload.iss).toBe('devkey');
    expect(payload.sub).toBe('alice');
    expect(payload.name).toBe('Alice');
    expect((payload.exp as number)).toBeGreaterThan(now);
    expect(payload.video).toMatchObject({
      roomJoin: true,
      room: 'demo',
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });
  });

  it('url defaults to ws://localhost:7880', async () => {
    const { url } = await generateToken('demo', 'alice', 'Alice');
    expect(url).toBe('ws://localhost:7880');
  });
});
