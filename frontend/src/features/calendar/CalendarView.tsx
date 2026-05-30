import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { useEventStore } from '../../stores/useEventStore';
import type { CalendarEvent, CalendarViewType } from './types';
import './styles.css';

interface CalendarViewProps {
  onEventClick?: (event: CalendarEvent) => void;
  onEventContextMenu?: (event: CalendarEvent, position: { x: number; y: number }) => void;
}

export default function CalendarView({ onEventClick, onEventContextMenu }: CalendarViewProps) {
  const { events, currentView, currentDate, setCurrentView, setCurrentDate, fetchEvents } = useEventStore();

  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.title,
    start: event.start,
    end: event.end,
    allDay: event.allDay,
    backgroundColor: event.color,
    borderColor: event.color,
    extendedProps: { location: event.location, description: event.description, priority: event.priority, originalEvent: event },
  }));

  return (
    <div className="calendar-view">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
        initialView={currentView}
        initialDate={currentDate}
        headerToolbar={{ left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek' }}
        buttonText={{ today: '今天', month: '月', week: '周', day: '日', list: '列表' }}
        locale="zh-cn"
        events={calendarEvents}
        editable={true}
        selectable={true}
        selectMirror={true}
        dayMaxEvents={3}
        weekends={true}
        height="calc(100vh - var(--topbar-height) - var(--space-8))"
        viewDidMount={(info) => { setCurrentView(info.view.type as CalendarViewType); }}
        datesSet={(info) => {
          setCurrentDate(info.view.currentStart);
          fetchEvents(info.start.toISOString(), info.end.toISOString());
        }}
        eventClick={(info) => { const originalEvent = info.event.extendedProps.originalEvent; if (originalEvent && onEventClick) { onEventClick(originalEvent); } }}
        eventDidMount={(info) => {
          if (onEventContextMenu) {
            info.el.addEventListener('contextmenu', (e) => {
              e.preventDefault();
              const originalEvent = info.event.extendedProps.originalEvent;
              if (originalEvent) {
                onEventContextMenu(originalEvent, { x: e.clientX, y: e.clientY });
              }
            });
          }
        }}
        select={(info) => { console.log('Date selected:', info.startStr, info.endStr); }}
        eventDrop={(info) => { console.log('Event dropped:', info.event.title, info.event.startStr); }}
      />
    </div>
  );
}
