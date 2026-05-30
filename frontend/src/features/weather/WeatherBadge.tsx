import { useState, useEffect } from 'react';
import { weatherApi } from '../../services/weatherApi';

interface WeatherData {
  temp: number;
  text: string;
  icon?: string;
}

export default function WeatherBadge() {
  const [weather, setWeather] = useState<WeatherData | null>(null);

  useEffect(() => {
    weatherApi
      .getNow()
      .then((resp) => {
        const data = resp.data?.data;
        if (data) {
          setWeather({ temp: data.temp, text: data.text, icon: data.icon });
        }
      })
      .catch(() => {
        // Weather fetch failed — silently ignore
      });
  }, []);

  if (!weather) return null;

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-1)',
        padding: 'var(--space-1) var(--space-2)',
        borderRadius: 'var(--radius-full)',
        background: 'var(--color-bg-secondary)',
        fontSize: 'var(--font-size-sm)',
        color: 'var(--color-text-secondary)',
        whiteSpace: 'nowrap',
      }}
    >
      {weather.icon && <span>{weather.icon}</span>}
      <span>{weather.temp}°C</span>
      <span>{weather.text}</span>
    </div>
  );
}
