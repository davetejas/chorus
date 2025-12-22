import React, { useEffect, useMemo, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';

type Line = {
  at: number;
  identity: string;
  text: string;
  isFinal: boolean;
  segmentId?: string;
};

export function TranscriptPanel() {
  const room = useRoomContext();
  const [lines, setLines] = useState<Line[]>([]);

  useEffect(() => {
    let disposed = false;

    // LiveKit text streams: receive lk.transcription topic
    // Docs show registerTextStreamHandler('lk.transcription', async (reader, participantInfo) => ...) citeturn41view3turn40view1
    const handler = async (reader: any, participantInfo: any) => {
      try {
        const message = await reader.readAll();
        const attrs = reader?.info?.attributes ?? {};
        const isFinal = attrs['lk.transcription_final'] === 'true';
        const segmentId = attrs['lk.segment_id'];

        if (disposed) return;
        setLines((prev) => [
          ...prev,
          {
            at: Date.now(),
            identity: participantInfo?.identity ?? 'unknown',
            text: String(message ?? ''),
            isFinal,
            segmentId,
          },
        ]);
      } catch (e) {
        // ignore stream read errors for POC
      }
    };

    room.registerTextStreamHandler?.('lk.transcription', handler);

    return () => {
      disposed = true;
      // There isn't a universal "unregister" API across all SDK versions; keep it simple for POC.
    };
  }, [room]);

  const rendered = useMemo(() => {
    return lines.slice(-200);
  }, [lines]);

  return (
    <div className="card" style={{ height: 540, overflow: 'auto' }}>
      <h3 style={{ marginTop: 0 }}>Live transcript</h3>
      <div className="small" style={{ marginBottom: 8, opacity: 0.75 }}>
        Topic: <code>lk.transcription</code>
      </div>
      {rendered.length === 0 ? (
        <div className="small">No transcript yet… start speaking.</div>
      ) : (
        rendered.map((l, i) => (
          <div key={`${l.at}-${i}`} style={{ marginBottom: 10 }}>
            <div className="small" style={{ opacity: 0.7 }}>
              [{l.identity}] {l.isFinal ? 'final' : 'interim'} {l.segmentId ? `· ${l.segmentId}` : ''}
            </div>
            <div>{l.text}</div>
          </div>
        ))
      )}
    </div>
  );
}
