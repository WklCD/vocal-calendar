import api from './api';

export const shareApi = {
  createLink: () => api.post('/share/create'),
  getShared: (token: string) => api.get(`/share/${token}`),
};
