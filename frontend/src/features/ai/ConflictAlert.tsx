import { useState, useEffect, useCallback } from 'react';
import { aiApi, type ConflictEvent } from '../../services/aiApi';

interface ConflictAlertProps {
  /** 新事件的开始时间 (ISO 格式) */
  startTime: string;
  /** 新事件的结束时间 (ISO 格式) */
  endTime: string;
  /** 关闭回调 */
  onDismiss: () => void;
}

/** 将 ISO 时间字符串格式化为 HH:MM */
function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export default function ConflictAlert({ startTime, endTime, onDismiss }: ConflictAlertProps) {
  const [conflicts, setConflicts] = useState<ConflictEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConflicts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await aiApi.detectConflicts(startTime, endTime);
      setConflicts(resp.data.data.conflicts);
    } catch {
      setError('检测冲突失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [startTime, endTime]);

  useEffect(() => {
    if (startTime && endTime) {
      fetchConflicts();
    }
  }, [startTime, endTime, fetchConflicts]);

  if (loading) {
    return (
      <div style={containerStyle}>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          正在检测时间冲突...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={containerStyle}>
        <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-sm)' }}>{error}</span>
        <button onClick={onDismiss} style={dismissBtnStyle}>
          关闭
        </button>
      </div>
    );
  }

  if (conflicts.length === 0) return null;

  return (
    <div role="alert" style={containerStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
        <span style={{ fontWeight: 600, fontSize: 'var(--font-size-base)', color: '#E65100' }}>
          ⚠️ 时间冲突提醒
        </span>
        <button onClick={onDismiss} aria-label="关闭冲突提醒" style={dismissBtnStyle}>
          ✕
        </button>
      </div>
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
        该时段与以下 {conflicts.length} 个事件冲突：
      </p>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {conflicts.map((evt) => (
          <li key={evt.id} style={conflictItemStyle}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: 'var(--radius-full)',
                background: evt.color || 'var(--color-secondary)',
                flexShrink: 0,
              }}
            />
            <span style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>{evt.title}</span>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
              {formatTime(evt.start_time)} - {formatTime(evt.end_time)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* --- Inline Styles --- */

const containerStyle: React.CSSProperties = {
  background: 'rgba(251, 188, 4, 0.08)',
  border: '1px solid rgba(251, 188, 4, 0.4)',
  borderRadius: 'var(--radius-lg)',
  padding: 'var(--space-4)',
};

const conflictItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 'var(--space-2)',
  padding: 'var(--space-2) var(--space-3)',
  background: 'var(--color-surface)',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--color-border-light)',
};

const dismissBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--color-text-secondary)',
  fontSize: 'var(--font-size-sm)',
  cursor: 'pointer',
  padding: 'var(--space-1)',
};
