import EventForm from './EventForm';
import type { CalendarEvent } from '../calendar/types';

interface EventModalProps {
  isOpen: boolean;
  event?: CalendarEvent | null;
  onSubmit: (data: any) => void;
  onClose: () => void;
}

export default function EventModal({ isOpen, event, onSubmit, onClose }: EventModalProps) {
  if (!isOpen) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-xl)', padding: 'var(--space-8)', width: '100%', maxWidth: '500px', maxHeight: '90vh', overflow: 'auto', boxShadow: 'var(--shadow-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-6)', fontSize: 'var(--font-size-xl)' }}>{event?.id ? '编辑事件' : '创建事件'}</h2>
        <EventForm initialData={event || undefined} onSubmit={onSubmit} onCancel={onClose} />
      </div>
    </div>
  );
}
