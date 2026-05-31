import { useCallback } from 'react';
import { useEventStore } from '../../stores/useEventStore';
import type { CalendarEvent } from '../calendar/types';

function formatICalDate(dateStr: string): string {
  const d = new Date(dateStr);
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}` +
    `T${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
  );
}

function generateICal(events: CalendarEvent[]): string {
  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//VocalCalendar//CN',
    'CALSCALE:GREGORIAN',
  ];

  events.forEach((ev) => {
    lines.push('BEGIN:VEVENT');
    lines.push(`UID:${ev.id}@vocal-calendar`);
    lines.push(`DTSTART:${ev.allDay ? ev.start.slice(0, 10).replace(/-/g, '') : formatICalDate(ev.start)}`);
    lines.push(`DTEND:${ev.allDay ? ev.end.slice(0, 10).replace(/-/g, '') : formatICalDate(ev.end)}`);
    lines.push(`SUMMARY:${ev.title}`);
    if (ev.description) lines.push(`DESCRIPTION:${ev.description}`);
    if (ev.location) lines.push(`LOCATION:${ev.location}`);
    lines.push('END:VEVENT');
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

export default function ExportMenu() {
  const events = useEventStore((s) => s.events);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  const handleExportICal = useCallback(() => {
    if (events.length === 0) return;
    const content = generateICal(events);
    const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vocal-calendar.ics';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [events]);

  const btnStyle: React.CSSProperties = {
    padding: 'var(--space-2) var(--space-4)',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--color-border)',
    background: 'var(--color-surface)',
    color: 'var(--color-text)',
    fontSize: 'var(--font-size-sm)',
    fontWeight: 500,
    cursor: 'pointer',
  };

  return (
    <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
      <button onClick={handlePrint} style={btnStyle}>
        打印/PDF
      </button>
      <button onClick={handleExportICal} style={btnStyle}>
        导出 iCal
      </button>
    </div>
  );
}
