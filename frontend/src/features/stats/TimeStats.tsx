import { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useEventStore } from '../../stores/useEventStore';

const COLORS = ['#4285F4', '#34A853', '#EA4335', '#FBBC04', '#9334E6', '#00ACC1', '#FF6D00', '#AB47BC'];

export default function TimeStats() {
  const events = useEventStore((s) => s.events);

  const data = useMemo(() => {
    if (events.length === 0) return [];

    const categoryMap: Record<string, number> = {};

    events.forEach((ev) => {
      const key = ev.categoryId || '未分类';
      const start = new Date(ev.start).getTime();
      const end = new Date(ev.end).getTime();
      const hours = Math.max((end - start) / (1000 * 60 * 60), 0);
      categoryMap[key] = (categoryMap[key] || 0) + hours;
    });

    return Object.entries(categoryMap).map(([name, value]) => ({
      name,
      value: Math.round(value * 10) / 10,
    }));
  }, [events]);

  if (data.length === 0) return null;

  return (
    <div style={{ width: '100%', height: 320 }}>
      <h3
        style={{
          margin: 0,
          marginBottom: 'var(--space-3)',
          fontSize: 'var(--font-size-base)',
          fontWeight: 600,
          color: 'var(--color-text)',
        }}
      >
        时间分布统计
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            dataKey="value"
            nameKey="name"
            label={({ name, value }) => `${name} ${value}h`}
          >
            {data.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${value} 小时`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
