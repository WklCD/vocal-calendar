import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import { shareApi } from '../../services/shareApi';

export default function PublicCalendar() {
  const { token } = useParams<{ token: string }>();
  const [events, setEvents] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    const fetchEvents = async () => {
      try {
        const resp = await shareApi.getShared(token);
        setEvents(resp.data.data);
      } catch {
        setError('分享链接无效或已过期');
      }
    };
    fetchEvents();
  }, [token]);

  if (error) {
    return (
      <div style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
        <h2>😕 {error}</h2>
      </div>
    );
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: 'var(--space-6)', color: 'var(--color-primary)' }}>📅 共享日程</h1>
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridMonth"
        locale="zh-cn"
        events={events}
        editable={false}
        height="auto"
      />
    </div>
  );
}
