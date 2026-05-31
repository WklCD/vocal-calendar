import api from './api';
import type { CalendarEvent } from '../features/calendar/types';

export const eventApi = {
  getEvents: (start: string, end: string) =>
    api.get<{ code: number; data: CalendarEvent[]; message: string }>(
      `/events?start=${start}&end=${end}`
    ),

  createEvent: (event: Omit<CalendarEvent, 'id'>) =>
    api.post<{ code: number; data: CalendarEvent; message: string }>('/events', event),

  updateEvent: (id: string, event: Partial<CalendarEvent>) =>
    api.put<{ code: number; data: CalendarEvent; message: string }>(`/events/${id}`, event),

  deleteEvent: (id: string) =>
    api.delete<{ code: number; data: null; message: string }>(`/events/${id}`),
};
