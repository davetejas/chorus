import { useRef, useEffect, useState } from 'react';
import { useChat } from '@livekit/components-react';

export function ChatPanel() {
  const { chatMessages, send, isSending } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;
    await send(text);
    setInput('');
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 280 }}>
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>Chat</h3>

      <div style={{ flex: 1, overflowY: 'auto', marginBottom: 8 }}>
        {chatMessages.length === 0 ? (
          <div className="small">No messages yet…</div>
        ) : (
          chatMessages.map((msg, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <div className="small" style={{ opacity: 0.7 }}>
                [{msg.from?.identity ?? 'unknown'}]
              </div>
              <div>{msg.message}</div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !isSending && handleSend()}
          placeholder="Type a message…"
          style={{ flex: 1 }}
        />
        <button
          className="btn"
          onClick={handleSend}
          disabled={isSending || !input.trim()}
          style={{ padding: '0 16px' }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
