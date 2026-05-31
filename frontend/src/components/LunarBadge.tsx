import { useState, useEffect } from 'react';
import { lunarApi } from '../services/lunarApi';

interface LunarDate {
  lunar_year: number;
  lunar_month: number;
  lunar_day: number;
  lunar_str: string;
  is_leap: boolean;
  festival: string | null;
  term: string | null;
}

interface LunarBadgeProps {
  year: number;
  month: number;
  day: number;
  showFull?: boolean;
}

export default function LunarBadge({ year, month, day, showFull = false }: LunarBadgeProps) {
  const [lunarInfo, setLunarInfo] = useState<LunarDate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLunar = async () => {
      try {
        setLoading(true);
        const data = await lunarApi.convertSolarToLunar(year, month, day);
        setLunarInfo(data);
        setError(null);
      } catch (err) {
        setError('获取农历信息失败');
        console.error('Lunar API error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLunar();
  }, [year, month, day]);

  if (loading) {
    return <span style={{ fontSize: '0.75rem', color: '#999' }}>加载中...</span>;
  }

  if (error || !lunarInfo) {
    return null;
  }

  const specialInfo = lunarInfo.festival || lunarInfo.term;

  if (showFull) {
    return (
      <div style={{
        fontSize: '0.875rem',
        color: '#666',
        lineHeight: 1.4,
      }}>
        <div>{lunarInfo.lunar_str}</div>
        {specialInfo && (
          <div style={{
            color: lunarInfo.festival ? '#e53935' : '#1976d2',
            fontWeight: 500,
          }}>
            {specialInfo}
          </div>
        )}
      </div>
    );
  }

  if (specialInfo) {
    return (
      <div style={{
        fontSize: '0.75rem',
        color: lunarInfo.festival ? '#e53935' : '#1976d2',
        fontWeight: 500,
      }}>
        {specialInfo}
      </div>
    );
  }

  return (
    <div style={{
      fontSize: '0.75rem',
      color: '#999',
    }}>
      {lunarInfo.lunar_month}月{lunarInfo.lunar_day}日
    </div>
  );
}
