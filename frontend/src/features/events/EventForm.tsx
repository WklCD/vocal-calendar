import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { CalendarEvent } from '../calendar/types';

const eventSchema = z.object({
  title: z.string().min(1, '请输入标题'),
  start_time: z.string().min(1, '请选择开始时间'),
  end_time: z.string().min(1, '请选择结束时间'),
  is_all_day: z.boolean().default(false),
  location: z.string().optional(),
  description: z.string().optional(),
  priority: z.number().min(1).max(5).default(3),
  color: z.string().optional(),
});

type EventFormData = z.infer<typeof eventSchema>;

interface EventFormProps {
  initialData?: Partial<CalendarEvent>;
  onSubmit: (data: EventFormData) => void;
  onCancel: () => void;
}

export default function EventForm({ initialData, onSubmit, onCancel }: EventFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EventFormData>({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      title: initialData?.title || '',
      start_time: initialData?.start ? initialData.start.slice(0, 16) : '',
      end_time: initialData?.end ? initialData.end.slice(0, 16) : '',
      is_all_day: initialData?.allDay || false,
      location: initialData?.location || '',
      description: initialData?.description || '',
      priority: initialData?.priority || 3,
      color: initialData?.color || '#4285F4',
    },
  });

  const colorOptions = [
    { value: '#4285F4', label: '蓝' },
    { value: '#EA4335', label: '红' },
    { value: '#34A853', label: '绿' },
    { value: '#FBBC04', label: '黄' },
    { value: '#9334E6', label: '紫' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div>
        <label htmlFor="title" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>标题</label>
        <input id="title" {...register('title')} placeholder="事件标题" style={{ width: '100%', padding: 'var(--space-3)', border: `1px solid ${errors.title ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-md)' }} />
        {errors.title && <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{errors.title.message}</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
        <div>
          <label htmlFor="start_time" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>开始时间</label>
          <input id="start_time" type="datetime-local" {...register('start_time')} style={{ width: '100%', padding: 'var(--space-3)', border: `1px solid ${errors.start_time ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-md)' }} />
        </div>
        <div>
          <label htmlFor="end_time" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>结束时间</label>
          <input id="end_time" type="datetime-local" {...register('end_time')} style={{ width: '100%', padding: 'var(--space-3)', border: `1px solid ${errors.end_time ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-md)' }} />
        </div>
      </div>

      <div>
        <label htmlFor="location" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>地点</label>
        <input id="location" {...register('location')} placeholder="可选" style={{ width: '100%', padding: 'var(--space-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }} />
      </div>

      <div>
        <label htmlFor="description" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>备注</label>
        <textarea id="description" {...register('description')} rows={3} placeholder="可选" style={{ width: '100%', padding: 'var(--space-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', resize: 'vertical' }} />
      </div>

      <div>
        <label style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>颜色</label>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          {colorOptions.map((opt) => (
            <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', cursor: 'pointer' }}>
              <input type="radio" value={opt.value} {...register('color')} />
              <span style={{ width: 20, height: 20, borderRadius: 'var(--radius-full)', background: opt.value }} />
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
        <button type="button" onClick={onCancel} style={{ padding: 'var(--space-2) var(--space-6)', background: 'transparent', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-secondary)' }}>取消</button>
        <button type="submit" disabled={isSubmitting} style={{ padding: 'var(--space-2) var(--space-6)', background: 'var(--color-primary)', color: 'var(--color-text-inverse)', borderRadius: 'var(--radius-md)', fontWeight: 600 }}>{initialData?.id ? '保存' : '创建'}</button>
      </div>
    </form>
  );
}
