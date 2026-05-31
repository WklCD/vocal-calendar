import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import VoiceButton from '../VoiceButton';

describe('VoiceButton', () => {
  it('renders the voice button', () => {
    render(<VoiceButton isListening={false} isSupported={true} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows microphone icon when not listening', () => {
    render(<VoiceButton isListening={false} isSupported={true} onToggle={() => {}} />);
    expect(screen.getByText('🎤')).toBeInTheDocument();
  });

  it('shows recording indicator when listening', () => {
    render(<VoiceButton isListening={true} isSupported={true} onToggle={() => {}} />);
    expect(screen.getByText('⏹️')).toBeInTheDocument();
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(<VoiceButton isListening={false} isSupported={true} onToggle={onToggle} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalled();
  });

  it('is disabled when not supported', () => {
    render(<VoiceButton isListening={false} isSupported={false} onToggle={() => {}} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
