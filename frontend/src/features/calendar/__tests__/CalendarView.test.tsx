import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CalendarView from '../CalendarView';
import { useEventStore } from '../../../stores/useEventStore';

describe('CalendarView', () => {
  beforeEach(() => {
    useEventStore.getState().loadMockEvents();
  });

  it('renders the calendar component', () => {
    render(<CalendarView />);
    expect(document.querySelector('.fc')).toBeInTheDocument();
  });

  it('displays mock events', () => {
    render(<CalendarView />);
    expect(screen.getByText('项目评审会议')).toBeInTheDocument();
  });
});
