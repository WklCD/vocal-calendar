import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ConflictAlert from '../ConflictAlert';
import { aiApi } from '../../../services/aiApi';

// Mock aiApi
vi.mock('../../../services/aiApi', () => ({
  aiApi: {
    detectConflicts: vi.fn(),
  },
}));

const mockedDetectConflicts = vi.mocked(aiApi.detectConflicts);

const mockConflicts = [
  {
    id: 1,
    title: '团队会议',
    start_time: '2026-05-30T10:00:00Z',
    end_time: '2026-05-30T11:00:00Z',
    color: '#4285F4',
  },
  {
    id: 2,
    title: '午餐',
    start_time: '2026-05-30T12:00:00Z',
    end_time: '2026-05-30T13:00:00Z',
  },
];

describe('ConflictAlert', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    mockedDetectConflicts.mockReturnValue(new Promise(() => {})); // never resolves
    render(<ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={vi.fn()} />);
    expect(screen.getByText('正在检测时间冲突...')).toBeInTheDocument();
  });

  it('renders conflicts when detected', async () => {
    mockedDetectConflicts.mockResolvedValue({
      data: { code: 0, data: { conflicts: mockConflicts }, message: 'ok' },
    } as any);
    render(<ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('团队会议')).toBeInTheDocument();
      expect(screen.getByText('午餐')).toBeInTheDocument();
    });
  });

  it('shows conflict count', async () => {
    mockedDetectConflicts.mockResolvedValue({
      data: { code: 0, data: { conflicts: mockConflicts }, message: 'ok' },
    } as any);
    render(<ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText(/2 个事件冲突/)).toBeInTheDocument();
    });
  });

  it('returns null when no conflicts', async () => {
    mockedDetectConflicts.mockResolvedValue({
      data: { code: 0, data: { conflicts: [] }, message: 'ok' },
    } as any);
    const { container } = render(
      <ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={vi.fn()} />,
    );
    await waitFor(() => {
      expect(container.innerHTML).toBe('');
    });
  });

  it('shows error state on API failure', async () => {
    mockedDetectConflicts.mockRejectedValue(new Error('Network error'));
    render(<ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('检测冲突失败，请重试')).toBeInTheDocument();
    });
  });

  it('calls onDismiss when close button is clicked', async () => {
    const onDismiss = vi.fn();
    mockedDetectConflicts.mockResolvedValue({
      data: { code: 0, data: { conflicts: mockConflicts }, message: 'ok' },
    } as any);
    render(<ConflictAlert startTime="2026-05-30T10:00:00Z" endTime="2026-05-30T11:00:00Z" onDismiss={onDismiss} />);
    await waitFor(() => {
      expect(screen.getByText('团队会议')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByLabelText('关闭冲突提醒'));
    expect(onDismiss).toHaveBeenCalled();
  });
});
