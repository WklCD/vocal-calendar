import api from './api';

export const holidayApi = {
  getHolidays: (year: number, month: number) =>
    api.get(`/holidays?year=${year}&month=${month}`),
  checkHoliday: (date: string) =>
    api.get(`/holidays/check?date=${date}`),
};
