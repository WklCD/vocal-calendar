import api from './api';

interface RegisterParams {
  email: string;
  username: string;
  password: string;
}

interface LoginParams {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface UserResponse {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  theme: string;
  created_at: string;
}

export const authApi = {
  register: (params: RegisterParams) =>
    api.post<{ code: number; data: UserResponse; message: string }>(
      '/auth/register',
      params
    ),

  login: (params: LoginParams) =>
    api.post<{ code: number; data: TokenResponse; message: string }>(
      '/auth/login',
      params
    ),

  refresh: (refreshToken: string) =>
    api.post<{ code: number; data: TokenResponse; message: string }>(
      '/auth/refresh',
      { refresh_token: refreshToken }
    ),

  getMe: () =>
    api.get<{ code: number; data: UserResponse; message: string }>('/auth/me'),

  updateMe: (data: { username?: string; theme?: string; avatar_url?: string }) =>
    api.put<{ code: number; data: UserResponse; message: string }>(
      '/auth/me',
      data
    ),
};
