import { useState, useCallback } from 'react';
import { shareApi } from '../../services/shareApi';

export default function ShareLink() {
  const [link, setLink] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCreate = useCallback(async () => {
    setLoading(true);
    setCopied(false);
    try {
      const resp = await shareApi.createLink();
      const token = resp.data?.data?.token;
      if (token) {
        setLink(`${window.location.origin}/share/${token}`);
      }
    } catch {
      // Share link creation failed
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCopy = useCallback(async () => {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard write failed — fallback: select text
    }
  }, [link]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <button
        onClick={handleCreate}
        disabled={loading}
        style={{
          padding: 'var(--space-2) var(--space-4)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          background: 'var(--color-primary)',
          color: 'var(--color-text-inverse)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 500,
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? '生成中...' : '生成分享链接'}
      </button>

      {link && (
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
          <input
            readOnly
            value={link}
            style={{
              flex: 1,
              padding: 'var(--space-2)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg-secondary)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text)',
            }}
          />
          <button
            onClick={handleCopy}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              background: copied ? 'var(--color-accent)' : 'var(--color-surface)',
              color: copied ? 'var(--color-text-inverse)' : 'var(--color-text)',
              fontSize: 'var(--font-size-sm)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {copied ? '已复制' : '复制'}
          </button>
        </div>
      )}
    </div>
  );
}
