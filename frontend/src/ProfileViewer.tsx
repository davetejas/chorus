import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';

export function ProfileViewer() {
  const room = useRoomContext();
  const [profileHtml, setProfileHtml] = useState<string | null>(null);

  useEffect(() => {
    const handler = (
      payload: Uint8Array,
      _participant: unknown,
      _kind: unknown,
      topic?: string,
    ) => {
      if (topic === 'onboard.profile') {
        setProfileHtml(new TextDecoder().decode(payload));
      }
    };

    room.on('dataReceived', handler);
    return () => { room.off('dataReceived', handler); };
  }, [room]);

  if (!profileHtml) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.75)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 100,
    }}>
      <div style={{ position: 'relative', width: '90%', maxWidth: 560, height: '80vh' }}>
        <button
          onClick={() => setProfileHtml(null)}
          aria-label="Close profile"
          style={{
            position: 'absolute', top: -14, right: -14, zIndex: 101,
            background: '#ef4444', color: '#fff', border: 'none',
            borderRadius: '50%', width: 32, height: 32,
            cursor: 'pointer', fontSize: 18, lineHeight: '32px',
          }}
        >
          ×
        </button>
        <iframe
          srcDoc={profileHtml}
          title="Your Onboarding Profile"
          sandbox="allow-same-origin"
          style={{ width: '100%', height: '100%', border: 'none', borderRadius: 12 }}
        />
      </div>
    </div>
  );
}
