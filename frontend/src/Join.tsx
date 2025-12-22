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
      <h1>AI Video Interview (POC)</h1>
      <p className="small">
        Candidate joins with video/audio. A Python agent joins the same LiveKit room and interviews you.
      </p>

      <div className="card" style={{ maxWidth: 520 }}>
        <label className="small">Room</label>
        <input className="input" value={props.room} onChange={(e) => props.setRoom(e.target.value)} />

        <div style={{ height: 12 }} />

        <label className="small">Your name</label>
        <input className="input" value={props.name} onChange={(e) => props.setName(e.target.value)} />

        <div style={{ height: 16 }} />

        <button className="btn" onClick={props.onJoin} disabled={props.busy || !props.room || !props.name}>
          {props.busy ? 'Joining…' : 'Join interview'}
        </button>

        {props.error ? (
          <p style={{ color: '#ff9aa2', marginTop: 12, whiteSpace: 'pre-wrap' }}>{props.error}</p>
        ) : null}

        <p className="small" style={{ marginTop: 12 }}>
          Tip: start the agent with <code>ROOM_NAME</code> set to the same room.
        </p>
      </div>
    </div>
  );
}
