import React from 'react';

export function Join(props: {
  room: string;
  name: string;
  setRoom: (v: string) => void;
  setName: (v: string) => void;
  onJoin: () => void;
  busy: boolean;
  error?: string | null;
}) {
  return (
    <div className="container">
      <h1>Customer Onboarding</h1>
      <p className="small">
        Join with video and audio. OnboardAI will guide you through identity verification, profile setup, and access configuration.
      </p>

      <div className="card" style={{ maxWidth: 520 }}>
        <label className="small">Room</label>
        <input className="input" value={props.room} onChange={(e) => props.setRoom(e.target.value)} />

        <div style={{ height: 12 }} />

        <label className="small">Your name</label>
        <input className="input" value={props.name} onChange={(e) => props.setName(e.target.value)} />

        <div style={{ height: 16 }} />

        <button className="btn" onClick={props.onJoin} disabled={props.busy || !props.room || !props.name}>
          {props.busy ? 'Joining…' : 'Start onboarding'}
        </button>

        {props.error ? (
          <p style={{ color: '#ff9aa2', marginTop: 12, whiteSpace: 'pre-wrap' }}>{props.error}</p>
        ) : null}

        <p className="small" style={{ marginTop: 12 }}>
          Ensure OnboardAI is running and set to the same room name.
        </p>
      </div>
    </div>
  );
}
