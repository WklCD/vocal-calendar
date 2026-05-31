import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import FreeSlotSuggest from '../FreeSlotSuggest';
import { aiApi } from '../../../services/aiApi';

// Mock aiApi
vi.mock('../../../services/aiApi', () => ({
  aiApi: {
    recommendSlot: vi.fn(),
  },
}));

const mockedRecommendSlot = vi.mocked(aiApi.recommendSlot);

const mockSlots = [
  { start: '2026-05-30T10:00:00Z', end: '2026-05-30T11:00:00Z' },
  { start: '2026-05-30T14:00:00Z', end: '2026-05-30T15:00:00Z' },
  { start: '2026-05-30T16:00:00Z', end: '2026-05-30T17:00:00Z' },
];

describe('FreeSlotSuggest', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.setSystemTime(new Date('2026-05-30T09:00:00'));
  });

  it('returns null while loading', () => {
    mockedRecommendSlot.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = render(<FreeSlotSuggest />);
    expect(container.innerHTML).toBe('');
  });

  it('returns null when no slots available', async () => {
    mockedRecommendSlot.mockResolvedValue({
      data: { code: 0, data: { slots: [] }, message: 'ok' },
    } as any);
    const { container } = render(<FreeSlotSuggest />);
    await waitFor(() => {
      expect(container.innerHTML).toBe('');
    });
  });

  it('renders slot buttons when slots are available', async () => {
    mockedRecommendSlot.mockResolvedValue({
      data: { code: 0, data: { slots: mockSlots }, message: 'ok' },
    } as any);
    render(<FreeSlotSuggest />);
    await waitFor(() => {
      expect(screen.getByText('💡 推荐空闲时段')).toBeInTheDocument();
    });
    // Should show up to 4 slots
    expect(screen.getAllByRole('button')).toHaveLength(3);
  });

  it('limits to 4 slots maximum', async () => {
    const fiveSlots = [
      ...mockSlots,
      { start: '2026-05-30T17:00:00Z', end: '2026-05-30T18:00:00Z' },
      { start: '2026-05-30T18:00:00Z', end: '2026-05-30T19:00:00Z' },
    ];
    mockedRecommendSlot.mockResolvedValue({
      data: { code: 0, data: { slots: fiveSlots }, message: 'ok' },
    } as any);
    render(<FreeSlotSuggest />);
    await waitFor(() => {
      expect(screen.getAllByRole('button')).toHaveLength(4);
    });
  });

  it('calls onSelect when a slot button is clicked', async () => {
    const onSelect = vi.fn();
    mockedRecommendSlot.mockResolvedValue({
      data: { code: 0, data: { slots: mockSlots }, message: 'ok' },
    } as any);
    render(<FreeSlotSuggest onSelect={onSelect} />);
    await waitFor(() => {
      expect(screen.getByText('💡 推荐空闲时段')).toBeInTheDocument();
    });
    const buttons = screen.getAllByRole('button');
    await userEvent.click(buttons[0]);
    expect(onSelect).toHaveBeenCalledWith('2026-05-30T10:00:00Z', '2026-05-30T11:00:00Z');
  });

  it('silently handles API failure', async () => {
    mockedRecommendSlot.mockRejectedValue(new Error('Network error'));
    const { container } = render(<FreeSlotSuggest />);
    await waitFor(() => {
      expect(container.innerHTML).toBe('');
    });
  });
});
