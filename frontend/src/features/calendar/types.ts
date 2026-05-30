export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  allDay: boolean;
  color?: string;
  location?: string;
  description?: string;
  categoryId?: string;
  priority?: number;
  recurrenceRule?: string;
}

export type CalendarViewType = 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay' | 'listWeek';

export interface CalendarState {
  currentDate: Date;
  currentView: CalendarViewType;
  setCurrentDate: (date: Date) => void;
  setCurrentView: (view: CalendarViewType) => void;
}
