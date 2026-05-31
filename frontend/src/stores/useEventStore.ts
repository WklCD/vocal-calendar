import { create } from 'zustand';
import type { CalendarEvent, CalendarViewType } from '../features/calendar/types';
import { eventApi } from '../services/eventApi';

interface EventState {
  events: CalendarEvent[];
  currentView: CalendarViewType;
  currentDate: Date;
  selectedEvent: CalendarEvent | null;
  loading: boolean;

  setEvents: (events: CalendarEvent[]) => void;
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
  removeEvent: (id: string) => void;
  setCurrentView: (view: CalendarViewType) => void;
  setCurrentDate: (date: Date) => void;
  setSelectedEvent: (event: CalendarEvent | null) => void;
  fetchEvents: (start: string, end: string) => Promise<void>;

  // Mock data for development (remove when backend is ready)
  loadMockEvents: () => void;
}

export const useEventStore = create<EventState>((set) => ({
  events: [],
  currentView: 'dayGridMonth',
  currentDate: new Date(),
  selectedEvent: null,
  loading: false,

  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  updateEvent: (id, updates) =>
    set((state) => ({
      events: state.events.map((e) => (e.id === id ? { ...e, ...updates } : e)),
    })),
  removeEvent: (id) =>
    set((state) => ({ events: state.events.filter((e) => e.id !== id) })),
  setCurrentView: (view) => set({ currentView: view }),
  setCurrentDate: (date) => set({ currentDate: date }),
  setSelectedEvent: (event) => set({ selectedEvent: event }),

  fetchEvents: async (start: string, end: string) => {
    set({ loading: true });
    try {
      const resp = await eventApi.getEvents(start, end);
      const rawEvents = resp.data.data as unknown as Array<Record<string, unknown>>;
      const events: CalendarEvent[] = rawEvents.map((e) => ({
        id: String(e.id),
        title: String(e.title),
        start: String(e.start_time),
        end: String(e.end_time),
        allDay: Boolean(e.is_all_day),
        color: e.color ? String(e.color) : undefined,
        location: e.location ? String(e.location) : undefined,
        description: e.description ? String(e.description) : undefined,
        categoryId: e.category_id ? String(e.category_id) : undefined,
        priority: typeof e.priority === 'number' ? e.priority : undefined,
        recurrenceRule: e.recurrence_rule ? String(e.recurrence_rule) : undefined,
      }));
      set({ events });
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      set({ loading: false });
    }
  },

  loadMockEvents: () => {
    const today = new Date();
    const y = today.getFullYear();
    const m = today.getMonth();
    const d = today.getDate();

    const mockEvents: CalendarEvent[] = [
      {
        id: '1',
        title: '项目评审会议',
        start: new Date(y, m, d, 10, 0).toISOString(),
        end: new Date(y, m, d, 11, 30).toISOString(),
        allDay: false,
        color: '#4285F4',
        location: '会议室A',
      },
      {
        id: '2',
        title: '午餐约会',
        start: new Date(y, m, d, 12, 0).toISOString(),
        end: new Date(y, m, d, 13, 0).toISOString(),
        allDay: false,
        color: '#34A853',
      },
      {
        id: '3',
        title: '产品需求讨论',
        start: new Date(y, m, d + 1, 14, 0).toISOString(),
        end: new Date(y, m, d + 1, 15, 30).toISOString(),
        allDay: false,
        color: '#FBBC04',
      },
      {
        id: '4',
        title: '周末团建',
        start: new Date(y, m, d + 3).toISOString(),
        end: new Date(y, m, d + 4).toISOString(),
        allDay: true,
        color: '#EA4335',
      },
      {
        id: '5',
        title: '代码审查',
        start: new Date(y, m, d, 15, 0).toISOString(),
        end: new Date(y, m, d, 16, 0).toISOString(),
        allDay: false,
        color: '#9334E6',
      },
    ];
    set({ events: mockEvents });
  },
}));
