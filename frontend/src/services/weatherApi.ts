import api from './api';

export const weatherApi = {
  getNow: (location?: string, lat?: number, lng?: number) => {
    let url = '/weather/now';
    const params: Record<string, string | number> = {};
    if (location) params.location = location;
    if (lat !== undefined && lng !== undefined) {
      params.lat = lat;
      params.lng = lng;
    }
    const query = new URLSearchParams(params).toString();
    return api.get(query ? `${url}?${query}` : url);
  },

  getForecast: (location?: string, lat?: number, lng?: number) => {
    let url = '/weather/forecast';
    const params: Record<string, string | number> = {};
    if (location) params.location = location;
    if (lat !== undefined && lng !== undefined) {
      params.lat = lat;
      params.lng = lng;
    }
    const query = new URLSearchParams(params).toString();
    return api.get(query ? `${url}?${query}` : url);
  },

  getCurrentLocation: (): Promise<{ latitude: number; longitude: number }> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by your browser'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    });
  },
};
