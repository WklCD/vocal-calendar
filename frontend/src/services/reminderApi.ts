import api from './api';

export interface Reminder {
  id: string;
  event_id: string;
  user_id: string;
  remind_at: string;
  type: string;
  status: string;
  created_at: string;
  event?: {
    id: string;
    title: string;
    start: string;
    end: string;
    color?: string;
    location?: string;
  };
}

export interface ReminderResponse {
  code: number;
  data: Reminder[];
  message: string;
}

export interface SingleReminderResponse {
  code: number;
  data: Reminder;
  message: string;
}

export const reminderApi = {
  getReminders: (status?: string) => {
    const params = status ? `?status=${status}` : '';
    return api.get<ReminderResponse>(`/reminders${params}`);
  },

  dismissReminder: (reminderId: string) =>
    api.put<SingleReminderResponse>(`/reminders/${reminderId}/dismiss`),
};
