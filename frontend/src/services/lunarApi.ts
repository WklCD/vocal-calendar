import api from './api';


export const lunarApi = {
  convertSolarToLunar: async (year: number, month: number, day: number) => {
    const response = await api.get(`/lunar/convert/${year}/${month}/${day}`);
    return response.data;
  },

  getMonthLunar: async (year: number, month: number) => {
    const response = await api.get(`/lunar/month/${year}/${month}`);
    return response.data;
  },

  getYearLunar: async (year: number) => {
    const response = await api.get(`/lunar/year/${year}`);
    return response.data;
  },

  getMonthFestivals: async (year: number, month: number) => {
    const response = await api.get(`/lunar/festivals/${year}/${month}`);
    return response.data;
  },

  getTodayLunar: async () => {
    const response = await api.get('/lunar/today');
    return response.data;
  },
};
