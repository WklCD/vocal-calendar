import { useEffect, useState } from 'react';
import { voiceApi } from '../../services/voiceApi';

interface HelpItem {
  command: string;
  example: string;
  description: string;
}

export default function VoiceHelpPanel() {
  const [items, setItems] = useState<HelpItem[]>([]);

  useEffect(() => {
    const fetchHelp = async () => {
      try {
        const resp = await voiceApi.getHelp();
        setItems(resp.data.data);
      } catch {
        // Handle error
      }
    };
    fetchHelp();
  }, []);

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-lg)' }}>
        💡 语音指令帮助
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {items.map((item, index) => (
          <div key={index} style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <span style={{
              padding: 'var(--space-1) var(--space-2)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}>
              {item.command}
            </span>
            <div>
              <p style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-1)' }}>
                {item.description}
              </p>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                例: &quot;{item.example}&quot;
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
