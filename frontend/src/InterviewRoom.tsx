import React from 'react';
import {
  LiveKitRoom,
  VideoConference,
  StartAudio,
} from '@livekit/components-react';
import { TranscriptPanel } from './TranscriptPanel';

export function InterviewRoom(props: {
  token: string;
  serverUrl: string;
  onLeave: () => void;
}) {
  return (
    <LiveKitRoom
      token={props.token}
      serverUrl={props.serverUrl}
      connect={true}
      video={true}
      audio={true}
      onDisconnected={props.onLeave}
      style={{ height: '100vh' }}
    >
      {/* Helps browsers that require a user gesture before playing audio */}
      <StartAudio label="Click to enable audio" />

      <div className="container">
        <div className="row">
          <div className="card">
            <VideoConference />
          </div>

          <TranscriptPanel />
        </div>

        <p className="small" style={{ marginTop: 12, opacity: 0.75 }}>
          If you don’t hear the agent, confirm the agent process joined the same room and your browser audio is enabled.
        </p>
      </div>
    </LiveKitRoom>
  );
}
