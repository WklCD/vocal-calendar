interface VoiceStatusProps {
  isListening: boolean;
  isProcessing: boolean;
  confidence: number;
  error: string | null;
}

export default function VoiceStatus({ isListening, isProcessing, confidence, error }: VoiceStatusProps) {
  if (error) {
    return (
      <div style={{ padding: 'var(--space-2) var(--space-3)', background: '#FEE2E2', color: 'var(--color-error)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
        ⚠️ {error}
      </div>
    );
  }

  if (isProcessing) {
    return (
      <div style={{ padding: 'var(--space-2) var(--space-3)', background: 'var(--color-primary)', color: 'var(--color-text-inverse)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <span style={{ animation: 'pulse 1.5s infinite' }}>⏳</span>
        正在处理...
      </div>
    );
  }

  if (isListening) {
    return (
      <div style={{ padding: 'var(--space-2) var(--space-3)', background: '#FEE2E2', color: 'var(--color-error)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-error)', animation: 'pulse 1s infinite' }} />
        正在录音... {confidence > 0 && `(${Math.round(confidence * 100)}%)`}
      </div>
    );
  }

  return null;
}
