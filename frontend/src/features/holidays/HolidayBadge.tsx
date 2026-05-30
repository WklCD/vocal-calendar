import { useState, useEffect } from 'react';
import { holidayApi } from '../../services/holidayApi';

interface Holiday {
  date: string;
  name: string;
}

interface HolidayBadgeProps {
  year: number;
  month: number;
}

export default function HolidayBadge({ year, month }: HolidayBadgeProps) {
  const [holidays, setHolidays] = useState<Holiday[]>([]);

  useEffect(() => {
    holidayApi
      .getHolidays(year, month)
      .then((resp) => {
        const data = resp.data?.data;
        if (Array.isArray(data) && data.length > 0) {
          setHolidays(data);
        }
      })
      .catch(() => {
        // Holiday fetch failed — silently ignore
      });
  }, [year, month]);

  if (holidays.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 'var(--space-1)',
      }}
    >
      {holidays.map((h) => (
        <span
          key={h.date}
          style={{
            display: 'inline-block',
            padding: 'var(--space-1) var(--space-2)',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(251, 188, 4, 0.15)',
            color: '#B06000',
            fontSize: 'var(--font-size-xs)',
            whiteSpace: 'nowrap',
          }}
        >
          {h.name}
        </span>
      ))}
    </div>
  );
}
