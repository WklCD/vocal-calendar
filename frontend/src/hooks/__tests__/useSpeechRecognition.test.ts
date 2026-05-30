import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSpeechRecognition } from '../useSpeechRecognition';

const mockStart = vi.fn();
const mockStop = vi.fn();
const mockAbort = vi.fn();

let lastInstance: any = null;

const MockSpeechRecognition = vi.fn().mockImplementation(function (this: any) {
  lastInstance = this;
  this.continuous = false;
  this.interimResults = false;
  this.lang = '';
  this.onresult = null;
  this.onerror = null;
  this.onend = null;
  this.onstart = null;
  this.start = vi.fn(() => {
    mockStart();
    if (this.onstart) this.onstart();
  });
  this.stop = vi.fn(() => {
    mockStop();
    if (this.onend) this.onend();
  });
  this.abort = vi.fn(() => {
    mockAbort();
  });
});

describe('useSpeechRecognition', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as any).SpeechRecognition = MockSpeechRecognition;
    (window as any).webkitSpeechRecognition = undefined;
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.isListening).toBe(false);
    expect(result.current.transcript).toBe('');
    expect(result.current.interimTranscript).toBe('');
    expect(result.current.isSupported).toBe(true);
  });

  it('starts listening', () => {
    const { result } = renderHook(() => useSpeechRecognition());
    act(() => { result.current.startListening(); });
    expect(mockStart).toHaveBeenCalled();
    expect(result.current.isListening).toBe(true);
  });

  it('stops listening', () => {
    const { result } = renderHook(() => useSpeechRecognition());
    act(() => { result.current.startListening(); });
    act(() => { result.current.stopListening(); });
    expect(mockStop).toHaveBeenCalled();
    expect(result.current.isListening).toBe(false);
  });

  it('detects unsupported browser', () => {
    (window as any).SpeechRecognition = undefined;
    (window as any).webkitSpeechRecognition = undefined;
    const { result } = renderHook(() => useSpeechRecognition());
    expect(result.current.isSupported).toBe(false);
  });

  it('resets transcript', () => {
    const { result } = renderHook(() => useSpeechRecognition());
    act(() => { result.current.resetTranscript(); });
    expect(result.current.transcript).toBe('');
    expect(result.current.interimTranscript).toBe('');
  });
});
