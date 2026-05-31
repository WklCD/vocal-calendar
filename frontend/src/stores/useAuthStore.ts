import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '../services/authApi';

interface User {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  theme: string;
  created_at: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateTheme: (theme: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const resp = await authApi.login({ email, password });
        const { access_token, refresh_token } = resp.data.data;
        set({
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        });
        await get().fetchUser();
      },

      register: async (email, username, password) => {
        await authApi.register({ email, username, password });
      },

      logout: () => {
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
      },

      fetchUser: async () => {
        try {
          const resp = await authApi.getMe();
          set({ user: resp.data.data });
        } catch {
          get().logout();
        }
      },

      updateTheme: async (theme) => {
        await authApi.updateMe({ theme });
        set((state) => ({
          user: state.user ? { ...state.user, theme } : null,
        }));
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
