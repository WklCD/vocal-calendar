import { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { useEventStore } from '../../stores/useEventStore';
import { lunarApi } from '../../services/lunarApi';
import type { CalendarEvent, CalendarViewType } from './types';
import './styles.css';

interface CalendarViewProps {
  onEventClick?: (event: CalendarEvent) => void;
  onEventContextMenu?: (event: CalendarEvent, position: { x: number; y: number }) => void;
}

interface LunarDay {
  lunar_day: number;
  festival?: string;
  term?: string;
}

interface LunarCache {
  [date: string]: LunarDay;
}

const DAY_CHARS = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];

const formatLunarDay = (day: number): string => {
  if (day <= 10) {
    return `初${DAY_CHARS[day]}`;
  } else if (day < 20) {
    return `十${DAY_CHARS[day - 10]}`;
  } else if (day === 20) {
    return '廿';
  } else if (day < 30) {
    return `廿${DAY_CHARS[day - 20]}`;
  } else {
    return '卅';
  }
};

const formatDateKey = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export default function CalendarView({ onEventClick, onEventContextMenu }: CalendarViewProps) {
  const { events, currentView, currentDate, setCurrentView, setCurrentDate, fetchEvents } = useEventStore();
  const [lunarCache, setLunarCache] = useState<LunarCache>({});

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

  useEffect(() => {
    const year = new Date().getFullYear();
    const month = new Date().getMonth() + 1;
    loadLunarCalendar(year, month);
  }, []);

  const loadLunarCalendar = async (year: number, month: number) => {
    try {
      const response = await lunarApi.getMonthLunar(year, month);
      const newCache: LunarCache = {};

      response.calendar.forEach((day: any) => {
        if (day.solar_date && day.lunar_day > 0) {
          newCache[day.solar_date] = {
            lunar_day: day.lunar_day,
            festival: day.festival,
            term: day.term,
          };
        }
      });

      setLunarCache(prev => ({ ...prev, ...newCache }));
    } catch (error) {
      console.error('Failed to load lunar calendar:', error);
    }
  };

  const handleDatesSet = (info: any) => {
    setCurrentDate(info.view.currentStart);
    fetchEvents(info.start.toISOString(), info.end.toISOString());

    const year = info.start.getFullYear();
    const month = info.start.getMonth() + 1;
    loadLunarCalendar(year, month);
  };

  const renderDayCellContent = (arg: any) => {
    const date = arg.date;
    const dateStr = formatDateKey(date);
    const lunarDay = lunarCache[dateStr];
    const dayNumber = arg.dayNumberText;

    let lunarText = '';
    let lunarClass = '';
    
    if (lunarDay) {
      if (lunarDay.festival) {
        lunarText = lunarDay.festival;
        lunarClass = 'festival';
      } else if (lunarDay.term) {
        lunarText = lunarDay.term;
        lunarClass = 'term';
      } else {
        lunarText = formatLunarDay(lunarDay.lunar_day);
        lunarClass = '';
      }
    }

    return (
      <div className="day-cell-content">
        <span className="day-number">{dayNumber}</span>
        {lunarText && <span className={`lunar-text ${lunarClass}`}>{lunarText}</span>}
      </div>
    );
  };

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
        height="100%"
        viewDidMount={(info) => { setCurrentView(info.view.type as CalendarViewType); }}
        datesSet={handleDatesSet}
        dayCellContent={renderDayCellContent}
        eventClick={(info) => {
          const originalEvent = info.event.extendedProps.originalEvent;
          if (originalEvent && onEventClick) {
            onEventClick(originalEvent);
          }
        }}
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
      />
    </div>
  );
}