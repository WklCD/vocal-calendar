import { useState, useEffect, useCallback } from 'react';
import { aiApi } from '../../services/aiApi';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';

/** 根据当前小时自动判断 morning / evening */
function autoDetectPeriod(): 'morning' | 'evening' {
  const hour = new Date().getHours();
  return hour >= 18 ? 'evening' : 'morning';
}

export default function DailyBriefing() {
  const [briefing, setBriefing] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { speak, stop, isSpeaking, isSupported } = useSpeechSynthesis();

  const period = autoDetectPeriod();
  const periodLabel = period === 'morning' ? '今日' : '明日';

  const fetchBriefing = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await aiApi.getDailyBriefing(period);
      setBriefing(resp.data.data.briefing);
    } catch {
      setError('获取摘要失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchBriefing();
  }, [fetchBriefing]);

  const handleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else if (briefing) {
      speak(briefing);
    }
  };

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={{ fontWeight: 700, fontSize: 'var(--font-size-lg)', color: 'var(--color-text-inverse)' }}>
          {period === 'morning' ? '☀️' : '🌙'} {periodLabel}日程摘要
        </span>
        {isSupported && briefing && (
          <button
            onClick={handleSpeak}
            aria-label={isSpeaking ? '停止播报' : '语音播报'}
            style={speakBtnStyle}
          >
            {isSpeaking ? '⏹️ 停止' : '🔊 播报'}
          </button>
        )}
      </div>

      {/* Body */}
      <div style={bodyStyle}>
        {loading && (
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            正在生成摘要...
          </span>
        )}
        {error && (
          <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-sm)' }}>{error}</span>
        )}
        {!loading && !error && briefing && (
          <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
            {briefing}
          </p>
        )}
      </div>
    </div>
  );
}

/* --- Inline Styles --- */

const cardStyle: React.CSSProperties = {
  borderRadius: 'var(--radius-xl)',
  overflow: 'hidden',
  boxShadow: 'var(--shadow-lg)',
  background: 'linear-gradient(135deg, var(--color-primary) 0%, #7C4DFF 100%)',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: 'var(--space-4) var(--space-5)',
};

const bodyStyle: React.CSSProperties = {
  background: 'var(--color-surface)',
  padding: 'var(--space-4) var(--space-5)',
  minHeight: 80,
};

const speakBtnStyle: React.CSSProperties = {
  background: 'rgba(255, 255, 255, 0.2)',
  border: '1px solid rgba(255, 255, 255, 0.3)',
  borderRadius: 'var(--radius-full)',
  color: 'var(--color-text-inverse)',
  fontSize: 'var(--font-size-xs)',
  fontWeight: 600,
  padding: 'var(--space-1) var(--space-3)',
  cursor: 'pointer',
};
