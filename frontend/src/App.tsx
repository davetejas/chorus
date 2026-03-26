import React, { useState } from 'react';
import { Join } from './Join';
import { generateToken } from './api';
import { OnboardRoom } from './OnboardRoom';

export default function App() {
  const [room, setRoom] = useState('demo');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [serverUrl, setServerUrl] = useState<string | null>(null);

  const join = async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await generateToken(room, name, name);
      setToken(res.token);
      setServerUrl(res.url);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setBusy(false);
    }
  };

  if (!token || !serverUrl) {
    return (
      <Join
        room={room}
        name={name}
        setRoom={setRoom}
        setName={setName}
        onJoin={join}
        busy={busy}
        error={err}
      />
    );
  }

  return (
    <OnboardRoom
      token={token}
      serverUrl={serverUrl}
      onLeave={() => {
        setToken(null);
        setServerUrl(null);
      }}
    />
  );
}

