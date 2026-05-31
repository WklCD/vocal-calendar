import { useState, useEffect } from 'react';
import { weatherApi } from '../../services/weatherApi';

interface WeatherData {
  temp: number;
  text: string;
  icon?: string;
  city?: string;
}

const CITIES = [
  { name: '北京', lat: 39.9042, lng: 116.4074 },
  { name: '上海', lat: 31.2304, lng: 121.4737 },
  { name: '广州', lat: 23.1291, lng: 113.2644 },
  { name: '深圳', lat: 22.5431, lng: 114.0579 },
  { name: '杭州', lat: 30.2741, lng: 120.1552 },
  { name: '成都', lat: 30.5728, lng: 104.0668 },
  { name: '重庆', lat: 29.4316, lng: 106.9123 },
  { name: '南京', lat: 32.0603, lng: 118.7969 },
];

export default function WeatherBadge() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const [showCitySelector, setShowCitySelector] = useState(false);

  const fetchWeather = async (lat?: number, lng?: number, cityName?: string) => {
    try {
      const resp = await weatherApi.getNow(undefined, lat, lng);
      const data = resp.data?.data;
      if (data) {
        setWeather({
          temp: Number(data.temp),
          text: data.text,
          icon: data.icon,
          city: cityName || data.city,
        });
        setLocationError(null);
      }
    } catch (error) {
      console.error('Failed to fetch weather:', error);
    }
  };

  useEffect(() => {
    const fetchWeatherWithLocation = async () => {
      try {
        const position = await weatherApi.getCurrentLocation();
        await fetchWeather(position.latitude, position.longitude);
      } catch (error) {
        const err = error as { code?: number; message?: string };
        let errorMsg = '无法获取位置';
        if (err.code === 1) errorMsg = '位置权限被拒绝';
        else if (err.code === 2) errorMsg = '无法获取位置信息';
        else if (err.code === 3) errorMsg = '获取位置超时';
        setLocationError(errorMsg);
        
        await fetchWeather();
      }
    };

    fetchWeatherWithLocation();
  }, []);

  const handleCityChange = (cityName: string) => {
    const city = CITIES.find(c => c.name === cityName);
    if (city) {
      fetchWeather(city.lat, city.lng, city.name);
      setSelectedCity(cityName);
    }
    setShowCitySelector(false);
  };

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
        position: 'relative',
      }}
    >
      {weather.icon && <span>{weather.icon}</span>}
      <div style={{ position: 'relative' }}>
        <span 
          style={{ fontSize: '0.8em', opacity: 0.7, cursor: 'pointer' }}
          onClick={() => setShowCitySelector(!showCitySelector)}
        >
          {weather.city}
        </span>
        {showCitySelector && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              marginTop: 'var(--space-1)',
              backgroundColor: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: 'var(--space-1)',
              zIndex: 100,
              minWidth: '100px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '0.75em', opacity: 0.6, marginBottom: 'var(--space-1)', padding: '0 var(--space-1)' }}>
              选择城市
            </div>
            {CITIES.map(city => (
              <div
                key={city.name}
                style={{
                  padding: 'var(--space-1)',
                  borderRadius: 'var(--radius-xs)',
                  cursor: 'pointer',
                  hover: { backgroundColor: 'var(--color-bg-secondary)' },
                }}
                onClick={() => handleCityChange(city.name)}
              >
                {city.name}
              </div>
            ))}
          </div>
        )}
      </div>
      <span>{weather.temp}°C</span>
      <span>{weather.text}</span>
      {locationError && (
        <span 
          style={{ fontSize: '0.7em', opacity: 0.5, cursor: 'help' }}
          title={locationError}
        >
          *
        </span>
      )}
    </div>
  );
}
