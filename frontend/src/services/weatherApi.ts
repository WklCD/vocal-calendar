import api from './api';

export const weatherApi = {
  getNow: (location?: string) =>
    api.get(`/weather/now${location ? `?location=${location}` : ''}`),
  getForecast: (location?: string) =>
    api.get(`/weather/forecast${location ? `?location=${location}` : ''}`),
};
