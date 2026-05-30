import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';

// Mock useAuthStore
vi.mock('../../../stores/useAuthStore', () => ({
  useAuthStore: () => ({
    login: vi.fn(),
    isAuthenticated: false,
  }),
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('LoginPage', () => {
  it('renders email input', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument();
  });

  it('renders password input', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument();
  });

  it('renders login button', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  it('renders register link', () => {
    renderWithRouter(<LoginPage />);
    expect(screen.getByText(/注册/i)).toBeInTheDocument();
  });
});
