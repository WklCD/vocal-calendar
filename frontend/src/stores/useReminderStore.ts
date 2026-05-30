import { create } from 'zustand';
import { reminderApi, type Reminder } from '../services/reminderApi';

interface ReminderState {
  reminders: Reminder[];
  activeReminder: Reminder | null;
  isToastVisible: boolean;

  fetchReminders: (status?: string) => Promise<void>;
  dismissReminder: (id: string) => Promise<void>;
  showToast: (reminder: Reminder) => void;
  hideToast: () => void;
  addReminder: (reminder: Reminder) => void;
  removeReminder: (id: string) => void;
}

export const useReminderStore = create<ReminderState>((set, get) => ({
  reminders: [],
  activeReminder: null,
  isToastVisible: false,

  fetchReminders: async (status?: string) => {
    try {
      const resp = await reminderApi.getReminders(status);
      set({ reminders: resp.data.data });
    } catch (error) {
      console.error('[ReminderStore] Failed to fetch reminders:', error);
    }
  },

  dismissReminder: async (id: string) => {
    try {
      await reminderApi.dismissReminder(id);
      set((state) => ({
        reminders: state.reminders.map((r) =>
          r.id === id ? { ...r, status: 'dismissed' } : r
        ),
        activeReminder:
          state.activeReminder?.id === id ? null : state.activeReminder,
        isToastVisible:
          state.activeReminder?.id === id ? false : state.isToastVisible,
      }));
    } catch (error) {
      console.error('[ReminderStore] Failed to dismiss reminder:', error);
    }
  },

  showToast: (reminder: Reminder) => {
    set({ activeReminder: reminder, isToastVisible: true });
  },

  hideToast: () => {
    set({ activeReminder: null, isToastVisible: false });
  },

  addReminder: (reminder: Reminder) => {
    set((state) => ({
      reminders: [...state.reminders, reminder],
    }));
  },

  removeReminder: (id: string) => {
    set((state) => ({
      reminders: state.reminders.filter((r) => r.id !== id),
      activeReminder: state.activeReminder?.id === id ? null : state.activeReminder,
      isToastVisible: state.activeReminder?.id === id ? false : state.isToastVisible,
    }));
  },
}));
