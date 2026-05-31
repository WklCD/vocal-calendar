import { useState, useEffect, useCallback } from 'react';
import { aiApi, type FreeSlot } from '../../services/aiApi';

interface FreeSlotSuggestProps {
  /** 选中空闲时段后的回调，参数为 [startISO, endISO] */
  onSelect?: (start: string, end: string) => void;
}

/** 获取今天的日期字符串 YYYY-MM-DD */
function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** 将 ISO 时间字符串格式化为 HH:MM */
function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export default function FreeSlotSuggest({ onSelect }: FreeSlotSuggestProps) {
  const [slots, setSlots] = useState<FreeSlot[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSlots = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await aiApi.recommendSlot(todayStr());
      setSlots(resp.data.data.slots.slice(0, 4));
    } catch {
      // 静默失败，不显示空闲推荐
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  if (loading || slots.length === 0) return null;

  return (
    <div style={containerStyle}>
      <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--color-accent)', marginBottom: 'var(--space-2)' }}>
        💡 推荐空闲时段
      </span>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        {slots.map((slot, i) => (
          <button
            key={i}
            onClick={() => onSelect?.(slot.start, slot.end)}
            style={slotBtnStyle}
          >
            {formatTime(slot.start)} - {formatTime(slot.end)}
          </button>
        ))}
      </div>
    </div>
  );
}

/* --- Inline Styles --- */

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  padding: 'var(--space-3)',
  background: 'rgba(52, 168, 83, 0.06)',
  border: '1px solid rgba(52, 168, 83, 0.25)',
  borderRadius: 'var(--radius-lg)',
};

const slotBtnStyle: React.CSSProperties = {
  padding: 'var(--space-2) var(--space-3)',
  background: 'var(--color-surface)',
  border: '1px solid rgba(52, 168, 83, 0.3)',
  borderRadius: 'var(--radius-full)',
  fontSize: 'var(--font-size-xs)',
  fontWeight: 500,
  color: 'var(--color-accent)',
  cursor: 'pointer',
  transition: 'var(--transition-fast)',
};
