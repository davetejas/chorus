import {
  LiveKitRoom,
  GridLayout,
  ParticipantTile,
  ControlBar,
  RoomAudioRenderer,
  LayoutContextProvider,
  StartAudio,
  useTracks,
} from '@livekit/components-react';
import { Track } from 'livekit-client';
import { TranscriptPanel } from './TranscriptPanel';
import { ChatPanel } from './ChatPanel';
import { ProfileViewer } from './ProfileViewer';

function VideoArea() {
  const tracks = useTracks(
    [{ source: Track.Source.Camera, withPlaceholder: true }],
    { onlySubscribed: false },
  );
  return (
    <LayoutContextProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <GridLayout tracks={tracks} style={{ flex: 1 }}>
          <ParticipantTile />
        </GridLayout>
        <ControlBar controls={{ screenShare: false }} />
      </div>
    </LayoutContextProvider>
  );
}

export function OnboardRoom(props: {
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
      <StartAudio label="Click to enable audio" />
      <RoomAudioRenderer />
      <ProfileViewer />

      <div className="container">
        <div className="row">
          <div className="card" style={{ flex: 1, minHeight: 480 }}>
            <VideoArea />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <TranscriptPanel />
            <ChatPanel />
          </div>
        </div>

        <p className="small" style={{ marginTop: 12, opacity: 0.75 }}>
          If you don't hear OnboardAI, confirm the agent container is running and joined the same room, and that your browser audio is enabled.
        </p>
      </div>
    </LiveKitRoom>
  );
}
