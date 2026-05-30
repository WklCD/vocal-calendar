import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { useState } from 'react';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码至少6位'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  if (isAuthenticated) {
    navigate('/calendar');
    return null;
  }

  const onSubmit = async (data: LoginForm) => {
    try {
      setError('');
      await login(data.email, data.password);
      navigate('/calendar');
    } catch {
      setError('邮箱或密码错误');
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--color-bg-secondary)',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        padding: 'var(--space-10)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-lg)',
        width: '100%',
        maxWidth: '400px',
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: 'var(--space-2)', color: 'var(--color-primary)' }}>
          Vocal Calendar
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-8)' }}>
          语音日历工具
        </p>

        {error && (
          <div style={{
            background: '#FEE2E2',
            color: 'var(--color-error)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
            fontSize: 'var(--font-size-sm)',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              邮箱
            </label>
            <input
              id="email"
              type="email"
              {...register('email')}
              placeholder="your@email.com"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.email ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
              }}
            />
            {errors.email && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.email.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              密码
            </label>
            <input
              id="password"
              type="password"
              {...register('password')}
              placeholder="••••••"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.password ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
              }}
            />
            {errors.password && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.password.message}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              background: 'var(--color-primary)',
              color: 'var(--color-text-inverse)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: 600,
              opacity: isSubmitting ? 0.7 : 1,
            }}
          >
            {isSubmitting ? '登录中...' : '登录'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
          还没有账户？{' '}
          <Link to="/register" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>
            立即注册
          </Link>
        </p>
      </div>
    </div>
  );
}
