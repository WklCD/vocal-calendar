import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const authStore = useAuthStore.getState();
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`;
  }
  return config;
});

export const exportImportApi = {
  exportEvents: async (format: 'ical' | 'json' | 'csv', options?: {
    startDate?: string;
    endDate?: string;
    categoryId?: string;
  }) => {
    const params = new URLSearchParams();
    params.append('format', format);

    if (options?.startDate) params.append('start_date', options.startDate);
    if (options?.endDate) params.append('end_date', options.endDate);
    if (options?.categoryId) params.append('category_id', options.categoryId);

    const response = await apiClient.get(`/export-import/events?${params.toString()}`, {
      responseType: 'blob',
    });

    return response;
  },

  importEvents: async (file: File, format: 'ical' | 'json' | 'csv') => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(
      `/export-import/events?format=${format}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  exportBackup: async () => {
    const response = await apiClient.get('/export-import/backup', {
      responseType: 'blob',
    });

    return response;
  },

  importBackup: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/export-import/backup', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  downloadTemplate: async (format: 'ical' | 'json' | 'csv') => {
    if (format === 'ical') {
      throw new Error('iCal template not available');
    }

    const response = await apiClient.get(`/export-import/template/${format}`, {
      responseType: 'blob',
    });

    return response;
  },
};
