import { useEffect, useState } from 'react';
import { voiceApi } from '../../services/voiceApi';

interface VoiceLog {
  id: string;
  raw_text: string;
  parsed_intent: string | null;
  response_text: string | null;
  created_at: string;
}

export default function VoiceHistory() {
  const [logs, setLogs] = useState<VoiceLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const resp = await voiceApi.getLogs();
        setLogs(resp.data.data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (loading) {
    return <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>加载中...</div>;
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: 'var(--space-6)', color: 'var(--color-primary)' }}>
        🎙️ 语音指令历史
      </h1>

      {logs.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          暂无语音指令记录
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {logs.map((log) => (
            <div
              key={log.id}
              style={{
                padding: 'var(--space-4)',
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                <span style={{ fontWeight: 600 }}>{log.raw_text}</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {new Date(log.created_at).toLocaleString('zh-CN')}
                </span>
              </div>
              {log.parsed_intent && (
                <span style={{
                  display: 'inline-block',
                  padding: 'var(--space-1) var(--space-2)',
                  background: 'rgba(66, 133, 244, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-primary)',
                  marginRight: 'var(--space-2)',
                }}>
                  {log.parsed_intent}
                </span>
              )}
              {log.response_text && (
                <p style={{ marginTop: 'var(--space-2)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  💬 {log.response_text}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
