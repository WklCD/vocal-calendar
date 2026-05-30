import { useEffect } from 'react';
import { useReminderStore } from '../../stores/useReminderStore';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';

export default function ReminderToast() {
  const { activeReminder, isToastVisible, hideToast, dismissReminder } =
    useReminderStore();
  const { speak, isSupported } = useSpeechSynthesis();

  // Auto-speak for voice/both type reminders
  useEffect(() => {
    if (!isToastVisible || !activeReminder) return;

    const reminderType = activeReminder.type;
    if (
      (reminderType === 'voice' || reminderType === 'both') &&
      isSupported
    ) {
      const title = activeReminder.event?.title ?? '您有一个提醒';
      speak(`提醒：${title}`);
    }
  }, [isToastVisible, activeReminder, speak, isSupported]);

  if (!isToastVisible || !activeReminder) return null;

  const eventTitle = activeReminder.event?.title ?? '未命名事件';
  const remindTime = new Date(activeReminder.remind_at).toLocaleTimeString(
    'zh-CN',
    { hour: '2-digit', minute: '2-digit' },
  );

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        position: 'fixed',
        top: 'var(--space-4)',
        right: 'var(--space-4)',
        zIndex: 9999,
        width: 360,
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        border: '1px solid var(--color-border)',
        animation: 'slideIn 0.3s ease-out',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding:
            'var(--space-3) var(--space-4)',
          background: 'var(--color-primary)',
          color: 'var(--color-text-inverse)',
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>
          提醒
        </span>
        <button
          onClick={hideToast}
          aria-label="关闭提醒"
          style={{
            background: 'transparent',
            color: 'var(--color-text-inverse)',
            fontSize: 'var(--font-size-lg)',
            lineHeight: 1,
            padding: 0,
          }}
        >
          &times;
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: 'var(--space-4)' }}>
        <p
          style={{
            fontWeight: 600,
            fontSize: 'var(--font-size-base)',
            marginBottom: 'var(--space-2)',
          }}
        >
          {eventTitle}
        </p>
        <p
          style={{
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          提醒时间：{remindTime}
        </p>
      </div>

      {/* Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 'var(--space-2)',
          padding:
            'var(--space-2) var(--space-4) var(--space-3)',
        }}
      >
        <button
          onClick={() => dismissReminder(activeReminder.id)}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          稍后提醒
        </button>
        <button
          onClick={hideToast}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
          }}
        >
          知道了
        </button>
      </div>
    </div>
  );
}
