import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DailyBriefing from '../DailyBriefing';
import { aiApi } from '../../../services/aiApi';

// Mock aiApi
vi.mock('../../../services/aiApi', () => ({
  aiApi: {
    getDailyBriefing: vi.fn(),
  },
}));

// Mock useSpeechSynthesis
const mockSpeak = vi.fn();
const mockStop = vi.fn();
vi.mock('../../../hooks/useSpeechSynthesis', () => ({
  useSpeechSynthesis: () => ({
    speak: mockSpeak,
    stop: mockStop,
    isSpeaking: false,
    isSupported: true,
    voices: [],
  }),
}));

const mockedGetDailyBriefing = vi.mocked(aiApi.getDailyBriefing);

describe('DailyBriefing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock morning time (hour < 18)
    vi.setSystemTime(new Date('2026-05-30T09:00:00'));
  });

  it('shows loading state initially', () => {
    mockedGetDailyBriefing.mockReturnValue(new Promise(() => {})); // never resolves
    render(<DailyBriefing />);
    expect(screen.getByText('正在生成摘要...')).toBeInTheDocument();
  });

  it('renders briefing content', async () => {
    mockedGetDailyBriefing.mockResolvedValue({
      data: { code: 0, data: { briefing: '今天有3个会议，第一个是上午10点的团队周会' }, message: 'ok' },
    } as any);
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText('今天有3个会议，第一个是上午10点的团队周会')).toBeInTheDocument();
    });
  });

  it('shows morning label before 18:00', async () => {
    vi.setSystemTime(new Date('2026-05-30T09:00:00'));
    mockedGetDailyBriefing.mockResolvedValue({
      data: { code: 0, data: { briefing: '摘要内容' }, message: 'ok' },
    } as any);
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText(/今日日程摘要/)).toBeInTheDocument();
    });
  });

  it('shows evening label after 18:00', async () => {
    vi.setSystemTime(new Date('2026-05-30T19:00:00'));
    mockedGetDailyBriefing.mockResolvedValue({
      data: { code: 0, data: { briefing: '摘要内容' }, message: 'ok' },
    } as any);
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText(/明日日程摘要/)).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    mockedGetDailyBriefing.mockRejectedValue(new Error('Network error'));
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText('获取摘要失败，请稍后重试')).toBeInTheDocument();
    });
  });

  it('renders speak button when briefing is loaded', async () => {
    mockedGetDailyBriefing.mockResolvedValue({
      data: { code: 0, data: { briefing: '摘要内容' }, message: 'ok' },
    } as any);
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText('🔊 播报')).toBeInTheDocument();
    });
  });

  it('calls speak when speak button is clicked', async () => {
    mockedGetDailyBriefing.mockResolvedValue({
      data: { code: 0, data: { briefing: '今天有会议' }, message: 'ok' },
    } as any);
    render(<DailyBriefing />);
    await waitFor(() => {
      expect(screen.getByText('🔊 播报')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('🔊 播报'));
    expect(mockSpeak).toHaveBeenCalledWith('今天有会议');
  });
});
