import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { useEventStore } from '../../stores/useEventStore';
import type { CalendarViewType } from './types';
import './styles.css';

export default function CalendarView() {
  const { events, currentView, currentDate, setCurrentView, setCurrentDate } =
    useEventStore();

  const handleViewChange = (view: CalendarViewType) => {
    setCurrentView(view);
  };

  const handleDateChange = (date: Date) => {
    setCurrentDate(date);
  };

  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.title,
    start: event.start,
    end: event.end,
    allDay: event.allDay,
    backgroundColor: event.color,
    borderColor: event.color,
    extendedProps: {
      location: event.location,
      description: event.description,
      priority: event.priority,
    },
  }));

  return (
    <div className="calendar-view">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
        initialView={currentView}
        initialDate={currentDate}
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
        }}
        buttonText={{
          today: '今天',
          month: '月',
          week: '周',
          day: '日',
          list: '列表',
        }}
        locale="zh-cn"
        events={calendarEvents}
        editable={true}
        selectable={true}
        selectMirror={true}
        dayMaxEvents={3}
        weekends={true}
        height="calc(100vh - var(--topbar-height) - var(--space-8))"
        viewDidMount={(info) => {
          handleViewChange(info.view.type as CalendarViewType);
        }}
        datesSet={(info) => {
          handleDateChange(info.view.currentStart);
        }}
        eventClick={(info) => {
          console.log('Event clicked:', info.event.title);
        }}
        select={(info) => {
          console.log('Date selected:', info.startStr, info.endStr);
        }}
        eventDrop={(info) => {
          console.log('Event dropped:', info.event.title, info.event.startStr);
        }}
      />
    </div>
  );
}
