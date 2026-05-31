import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { useState } from 'react';

const registerSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  username: z.string().min(2, '用户名至少2位'),
  password: z.string().min(6, '密码至少6位'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: '两次密码不一致',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: registerUser } = useAuthStore();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      setError('');
      await registerUser(data.email, data.username, data.password);
      navigate('/login');
    } catch {
      setError('注册失败，邮箱可能已被使用');
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
          创建账户
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-8)' }}>
          加入 Vocal Calendar
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
              }}
            />
            {errors.email && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.email.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="username" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              用户名
            </label>
            <input
              id="username"
              type="text"
              {...register('username')}
              placeholder="你的名字"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.username ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.username && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.username.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              密码
            </label>
            <input
              id="password"
              type="password"
              {...register('password')}
              placeholder="至少6位"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.password ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.password && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.password.message}
              </span>
            )}
          </div>

          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="confirmPassword" style={{ display: 'block', marginBottom: 'var(--space-1)', fontWeight: 500 }}>
              确认密码
            </label>
            <input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword')}
              placeholder="再次输入密码"
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                border: `1px solid ${errors.confirmPassword ? 'var(--color-error)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            />
            {errors.confirmPassword && (
              <span style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>
                {errors.confirmPassword.message}
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
            }}
          >
            {isSubmitting ? '注册中...' : '注册'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
          已有账户？{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 500 }}>
            立即登录
          </Link>
        </p>
      </div>
    </div>
  );
}
