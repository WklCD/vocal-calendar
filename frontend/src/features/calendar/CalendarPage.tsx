import CalendarView from './CalendarView';
import { useAuthStore } from '../../stores/useAuthStore';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useEventStore } from '../../stores/useEventStore';

export default function CalendarPage() {
  const { user, logout } = useAuthStore();
  const { loadMockEvents } = useEventStore();
  const navigate = useNavigate();

  useEffect(() => {
    loadMockEvents();
  }, [loadMockEvents]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top Bar */}
      <header
        style={{
          height: 'var(--topbar-height)',
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-6)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-primary)' }}>
            📅 Vocal Calendar
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {user?.username}
          </span>
          <button
            onClick={handleLogout}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
              cursor: 'pointer',
            }}
          >
            退出
          </button>
        </div>
      </header>

      {/* Calendar Content */}
      <main style={{ flex: 1, padding: 'var(--space-4)', overflow: 'hidden' }}>
        <CalendarView />
      </main>
    </div>
  );
}
