import { useState } from 'react';
import CalendarView from './CalendarView';
import EventModal from '../events/EventModal';
import EventContextMenu from '../events/EventContextMenu';
import VoicePanel from '../voice/VoicePanel';
import ReminderToast from '../reminders/ReminderToast';
import DailyBriefing from '../ai/DailyBriefing';
import FreeSlotSuggest from '../ai/FreeSlotSuggest';
import VoiceSelector from '../settings/VoiceSelector';
import { useAuthStore } from '../../stores/useAuthStore';
import { useEventStore } from '../../stores/useEventStore';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import type { CalendarEvent } from './types';

export default function CalendarPage() {
  const { user, logout } = useAuthStore();
  const { fetchEvents, addEvent, updateEvent, removeEvent } = useEventStore();
  const navigate = useNavigate();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [contextMenu, setContextMenu] = useState<{ isOpen: boolean; position: { x: number; y: number }; event: CalendarEvent | null }>({ isOpen: false, position: { x: 0, y: 0 }, event: null });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59).toISOString();
    fetchEvents(start, end);
    // Fallback: loadMockEvents() for development without backend
  }, [fetchEvents]);

  const handleLogout = () => { logout(); navigate('/login'); };

  const handleCreateEvent = () => { setEditingEvent(null); setIsModalOpen(true); };

  const handleSubmitEvent = (data: any) => {
    if (editingEvent?.id) {
      updateEvent(editingEvent.id, { title: data.title, start: data.start_time, end: data.end_time, allDay: data.is_all_day, location: data.location, description: data.description, priority: data.priority, color: data.color });
    } else {
      addEvent({ id: Date.now().toString(), title: data.title, start: data.start_time, end: data.end_time, allDay: data.is_all_day, location: data.location, description: data.description, priority: data.priority, color: data.color });
    }
    setIsModalOpen(false);
    setEditingEvent(null);
  };

  const handleDeleteEvent = () => {
    if (contextMenu.event?.id) { removeEvent(contextMenu.event.id); }
    setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{ height: 'var(--topbar-height)', background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 var(--space-6)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-primary)' }}>Vocal Calendar</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <button onClick={handleCreateEvent} style={{ padding: 'var(--space-2) var(--space-4)', background: 'var(--color-primary)', color: 'var(--color-text-inverse)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>+ 新建事件</button>
          <button
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
            style={{
              padding: 'var(--space-2)',
              background: isSettingsOpen ? 'var(--color-primary)' : 'transparent',
              color: isSettingsOpen ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-lg)',
              border: isSettingsOpen ? 'none' : '1px solid var(--color-border)',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            title="设置"
          >
            ⚙️
          </button>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>{user?.username}</span>
          <button onClick={handleLogout} style={{ padding: 'var(--space-2) var(--space-4)', background: 'transparent', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>退出</button>
        </div>
      </header>

      {isSettingsOpen && (
        <div style={{
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          maxHeight: '400px',
          overflowY: 'auto',
          flexShrink: 0,
        }}>
          <VoiceSelector />
        </div>
      )}

      <main style={{ flex: 1, padding: 'var(--space-4)', overflow: 'hidden' }}>
        <DailyBriefing />
        <FreeSlotSuggest />
        <CalendarView onEventClick={(event) => { setEditingEvent(event); setIsModalOpen(true); }} onEventContextMenu={(event, position) => { setContextMenu({ isOpen: true, position, event }); }} />
      </main>

      <EventModal isOpen={isModalOpen} event={editingEvent} onSubmit={handleSubmitEvent} onClose={() => { setIsModalOpen(false); setEditingEvent(null); }} />

      <EventContextMenu isOpen={contextMenu.isOpen} position={contextMenu.position} onEdit={() => { setEditingEvent(contextMenu.event); setIsModalOpen(true); setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null }); }} onDelete={handleDeleteEvent} onClose={() => setContextMenu({ isOpen: false, position: { x: 0, y: 0 }, event: null })} />

      <ReminderToast />
      <VoicePanel />
    </div>
  );
}
