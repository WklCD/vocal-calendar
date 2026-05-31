import { useState, useRef } from 'react';

interface VoiceButtonProps {
  isListening: boolean;
  isSupported: boolean;
  onToggle: () => void;
}

export default function VoiceButton({ isListening, isSupported, onToggle }: VoiceButtonProps) {
  const [isPressed, setIsPressed] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  if (!isSupported) {
    return (
      <button disabled title="您的浏览器不支持语音识别" style={{ width: 48, height: 48, borderRadius: 'var(--radius-full)', background: 'var(--color-border)', color: 'var(--color-text-disabled)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'not-allowed', opacity: 0.5 }}>
        🎤
      </button>
    );
  }

  return (
    <button
      ref={buttonRef}
      onClick={onToggle}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      style={{
        width: 48,
        height: 48,
        borderRadius: 'var(--radius-full)',
        background: isListening ? 'var(--color-error)' : isPressed ? 'var(--color-primary-dark)' : 'var(--color-primary)',
        color: 'var(--color-text-inverse)',
        fontSize: '1.2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all var(--transition-fast)',
        transform: isPressed ? 'scale(0.95)' : 'scale(1)',
        boxShadow: isListening ? '0 0 0 4px rgba(234, 67, 53, 0.3)' : 'var(--shadow-md)',
        animation: isListening ? 'pulse 1.5s infinite' : 'none',
      }}
      aria-label={isListening ? '停止录音' : '开始语音'}
    >
      {isListening ? '⏹️' : '🎤'}
    </button>
  );
}
