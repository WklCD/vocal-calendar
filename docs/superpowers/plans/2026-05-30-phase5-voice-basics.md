# Phase 5: 语音交互基础 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 Web Speech API 实现语音识别和语音合成，封装为 React Hook，创建语音按钮 UI（按住说话）、录音波形可视化、实时转文字显示、浏览器兼容性检测、语音状态管理。

**Architecture:** 前端使用 Web Speech API 的 SpeechRecognition（语音识别）和 SpeechSynthesis（语音合成），封装为 useSpeechRecognition 和 useSpeechSynthesis 两个 Hook。波形可视化使用 Web Audio API + Canvas。状态通过 Zustand useVoiceStore 管理。

**Tech Stack:** Web Speech API, Web Audio API, Canvas, React 18, TypeScript, Zustand

---

## File Structure

| File | Responsibility |
|------|---------------|
| `frontend/src/hooks/useSpeechRecognition.ts` | 语音识别 Hook |
| `frontend/src/hooks/useSpeechSynthesis.ts` | 语音合成 Hook |
| `frontend/src/hooks/useAudioVisualizer.ts` | 音频波形可视化 Hook |
| `frontend/src/features/voice/VoiceButton.tsx` | 语音按钮组件（按住说话） |
| `frontend/src/features/voice/VoicePanel.tsx` | 语音交互面板 |
| `frontend/src/features/voice/WaveformVisualizer.tsx` | 波形可视化组件 |
| `frontend/src/features/voice/VoiceStatus.tsx` | 语音状态指示器 |
| `frontend/src/stores/useVoiceStore.ts` | 语音状态管理 |
| `frontend/src/hooks/__tests__/useSpeechRecognition.test.ts` | 识别 Hook 测试 |
| `frontend/src/features/voice/__tests__/VoiceButton.test.tsx` | 语音按钮测试 |

---

## Task 1: 创建 useSpeechRecognition Hook

**Files:**
- Create: `frontend/src/hooks/useSpeechRecognition.ts`
- Create: `frontend/src/hooks/__tests__/useSpeechRecognition.test.ts`

- [ ] **Step 1: 编写 Hook 测试 (RED)**

创建 `frontend/src/hooks/__tests__/useSpeechRecognition.test.ts`：

```typescript
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSpeechRecognition } from '../useSpeechRecognition';

// Mock SpeechRecognition
const mockStart = vi.fn();
const mockStop = vi.fn();
const mockAbort = vi.fn();

const MockSpeechRecognition = vi.fn().mockImplementation(() => ({
  start: mockStart,
  stop: mockStop,
  abort: mockAbort,
  continuous: false,
  interimResults: false,
  lang: '',
  onresult: null,
  onerror: null,
  onend: null,
  onstart: null,
}));

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
    act(() => {
      result.current.startListening();
    });
    expect(mockStart).toHaveBeenCalled();
    expect(result.current.isListening).toBe(true);
  });

  it('stops listening', () => {
    const { result } = renderHook(() => useSpeechRecognition());
    act(() => {
      result.current.startListening();
    });
    act(() => {
      result.current.stopListening();
    });
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
    act(() => {
      result.current.resetTranscript();
    });
    expect(result.current.transcript).toBe('');
    expect(result.current.interimTranscript).toBe('');
  });
});
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/hooks/__tests__/useSpeechRecognition.test.ts
```

Expected: FAIL — `Cannot find module '../useSpeechRecognition'`

- [ ] **Step 3: 实现 useSpeechRecognition Hook**

创建 `frontend/src/hooks/useSpeechRecognition.ts`：

```typescript
import { useState, useEffect, useRef, useCallback } from 'react';

interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  confidence: number;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);

  const SpeechRecognition =
    typeof window !== 'undefined'
      ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null;

  const isSupported = !!SpeechRecognition;

  useEffect(() => {
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      isListeningRef.current = true;
      setError(null);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
          setConfidence(result[0].confidence);
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalTranscript) {
        setTranscript((prev) => prev + finalTranscript);
      }
      setInterimTranscript(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== 'aborted') {
        setError(`语音识别错误: ${event.error}`);
      }
      setIsListening(false);
      isListeningRef.current = false;
    };

    recognition.onend = () => {
      setIsListening(false);
      isListeningRef.current = false;
    };

    recognitionRef.current = recognition;

    return () => {
      if (isListeningRef.current) {
        recognition.stop();
      }
    };
  }, [SpeechRecognition]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListeningRef.current) {
      setTranscript('');
      setInterimTranscript('');
      setError(null);
      try {
        recognitionRef.current.start();
      } catch (e) {
        // Already started
      }
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListeningRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setConfidence(0);
    setError(null);
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    confidence,
    isSupported,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}
```

- [ ] **Step 4: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/hooks/__tests__/useSpeechRecognition.test.ts
```

Expected: `5 passed`

- [ ] **Step 5: 提交**

```bash
git add frontend/
git commit -m "feat: add useSpeechRecognition hook with Web Speech API"
```

---

## Task 2: 创建 useSpeechSynthesis Hook

**Files:**
- Create: `frontend/src/hooks/useSpeechSynthesis.ts`

- [ ] **Step 1: 创建 useSpeechSynthesis Hook**

创建 `frontend/src/hooks/useSpeechSynthesis.ts`：

```typescript
import { useState, useCallback, useEffect } from 'react';

interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  stop: () => void;
  isSpeaking: boolean;
  isSupported: boolean;
  voices: SpeechSynthesisVoice[];
}

export function useSpeechSynthesis(): UseSpeechSynthesisReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  const isSupported =
    typeof window !== 'undefined' && 'speechSynthesis' in window;

  useEffect(() => {
    if (!isSupported) return;

    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [isSupported]);

  const speak = useCallback(
    (text: string) => {
      if (!isSupported) return;

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-CN';
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;

      // Try to find a Chinese voice
      const chineseVoice = voices.find(
        (v) => v.lang.startsWith('zh') || v.lang.includes('CN')
      );
      if (chineseVoice) {
        utterance.voice = chineseVoice;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    },
    [isSupported, voices]
  );

  const stop = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [isSupported]);

  return { speak, stop, isSpeaking, isSupported, voices };
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/
git commit -m "feat: add useSpeechSynthesis hook for text-to-speech"
```

---

## Task 3: 创建 useAudioVisualizer Hook

**Files:**
- Create: `frontend/src/hooks/useAudioVisualizer.ts`

- [ ] **Step 1: 创建音频可视化 Hook**

创建 `frontend/src/hooks/useAudioVisualizer.ts`：

```typescript
import { useRef, useCallback, useEffect, useState } from 'react';

interface UseAudioVisualizerReturn {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  startVisualization: (stream: MediaStream) => void;
  stopVisualization: () => void;
  isActive: boolean;
}

export function useAudioVisualizer(): UseAudioVisualizerReturn {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const [isActive, setIsActive] = useState(false);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;

    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);

    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = getComputedStyle(document.documentElement)
      .getPropertyValue('--color-bg-secondary')
      .trim() || '#F8F9FA';
    ctx.fillRect(0, 0, width, height);

    ctx.lineWidth = 2;
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, '#4285F4');
    gradient.addColorStop(0.5, '#34A853');
    gradient.addColorStop(1, '#EA4335');
    ctx.strokeStyle = gradient;

    ctx.beginPath();

    const sliceWidth = width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * height) / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(width, height / 2);
    ctx.stroke();

    animationFrameRef.current = requestAnimationFrame(draw);
  }, []);

  const startVisualization = useCallback(
    (stream: MediaStream) => {
      try {
        const audioContext = new (window.AudioContext ||
          (window as any).webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;

        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        setIsActive(true);

        draw();
      } catch (e) {
        console.error('Failed to start audio visualization:', e);
      }
    },
    [draw]
  );

  const stopVisualization = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setIsActive(false);

    // Clear canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, []);

  useEffect(() => {
    return () => {
      stopVisualization();
    };
  }, [stopVisualization]);

  return { canvasRef, startVisualization, stopVisualization, isActive };
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/
git commit -m "feat: add useAudioVisualizer hook for waveform display"
```

---

## Task 4: 创建语音状态管理 Store

**Files:**
- Create: `frontend/src/stores/useVoiceStore.ts`

- [ ] **Step 1: 创建 useVoiceStore**

创建 `frontend/src/stores/useVoiceStore.ts`：

```typescript
import { create } from 'zustand';

interface VoiceSession {
  lastIntent: string | null;
  lastEntities: Record<string, any> | null;
  turnCount: number;
}

interface VoiceState {
  isRecording: boolean;
  transcript: string;
  interimTranscript: string;
  confidence: number;
  isProcessing: boolean;
  response: string | null;
  session: VoiceSession;

  setRecording: (recording: boolean) => void;
  setTranscript: (text: string) => void;
  setInterimTranscript: (text: string) => void;
  setConfidence: (confidence: number) => void;
  setProcessing: (processing: boolean) => void;
  setResponse: (response: string | null) => void;
  updateSession: (intent: string, entities: Record<string, any>) => void;
  clearSession: () => void;
  reset: () => void;
}

export const useVoiceStore = create<VoiceState>((set) => ({
  isRecording: false,
  transcript: '',
  interimTranscript: '',
  confidence: 0,
  isProcessing: false,
  response: null,
  session: {
    lastIntent: null,
    lastEntities: null,
    turnCount: 0,
  },

  setRecording: (recording) => set({ isRecording: recording }),
  setTranscript: (text) => set({ transcript: text }),
  setInterimTranscript: (text) => set({ interimTranscript: text }),
  setConfidence: (confidence) => set({ confidence }),
  setProcessing: (processing) => set({ isProcessing: processing }),
  setResponse: (response) => set({ response }),

  updateSession: (intent, entities) =>
    set((state) => ({
      session: {
        lastIntent: intent,
        lastEntities: entities,
        turnCount: state.session.turnCount + 1,
      },
    })),

  clearSession: () =>
    set({
      session: { lastIntent: null, lastEntities: null, turnCount: 0 },
    }),

  reset: () =>
    set({
      isRecording: false,
      transcript: '',
      interimTranscript: '',
      confidence: 0,
      isProcessing: false,
      response: null,
    }),
}));
```

- [ ] **Step 2: 提交**

```bash
git add frontend/
git commit -m "feat: add useVoiceStore for voice interaction state management"
```

---

## Task 5: 创建波形可视化组件

**Files:**
- Create: `frontend/src/features/voice/WaveformVisualizer.tsx`

- [ ] **Step 1: 创建 WaveformVisualizer**

创建 `frontend/src/features/voice/WaveformVisualizer.tsx`：

```tsx
import { useAudioVisualizer } from '../../hooks/useAudioVisualizer';

interface WaveformVisualizerProps {
  stream: MediaStream | null;
  isActive: boolean;
}

export default function WaveformVisualizer({ stream, isActive }: WaveformVisualizerProps) {
  const { canvasRef, startVisualization, stopVisualization } = useAudioVisualizer();

  if (isActive && stream) {
    startVisualization(stream);
  } else {
    stopVisualization();
  }

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={60}
      style={{
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        width: '100%',
        height: '60px',
        opacity: isActive ? 1 : 0.3,
        transition: 'opacity var(--transition-normal)',
      }}
    />
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/
git commit -m "feat: add WaveformVisualizer component"
```

---

## Task 6: 创建语音按钮和语音面板

**Files:**
- Create: `frontend/src/features/voice/VoiceButton.tsx`
- Create: `frontend/src/features/voice/VoicePanel.tsx`
- Create: `frontend/src/features/voice/VoiceStatus.tsx`
- Create: `frontend/src/features/voice/__tests__/VoiceButton.test.tsx`

- [ ] **Step 1: 编写 VoiceButton 测试 (RED)**

创建 `frontend/src/features/voice/__tests__/VoiceButton.test.tsx`：

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import VoiceButton from '../VoiceButton';

describe('VoiceButton', () => {
  it('renders the voice button', () => {
    render(
      <VoiceButton
        isListening={false}
        isSupported={true}
        onToggle={() => {}}
      />
    );
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows microphone icon when not listening', () => {
    render(
      <VoiceButton
        isListening={false}
        isSupported={true}
        onToggle={() => {}}
      />
    );
    expect(screen.getByText('🎤')).toBeInTheDocument();
  });

  it('shows recording indicator when listening', () => {
    render(
      <VoiceButton
        isListening={true}
        isSupported={true}
        onToggle={() => {}}
      />
    );
    expect(screen.getByText('⏹️')).toBeInTheDocument();
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(
      <VoiceButton
        isListening={false}
        isSupported={true}
        onToggle={onToggle}
      />
    );
    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalled();
  });

  it('is disabled when not supported', () => {
    render(
      <VoiceButton
        isListening={false}
        isSupported={false}
        onToggle={() => {}}
      />
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

- [ ] **Step 2: 运行测试确认失败 (RED)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/voice/__tests__/VoiceButton.test.tsx
```

Expected: FAIL

- [ ] **Step 3: 创建 VoiceStatus**

创建 `frontend/src/features/voice/VoiceStatus.tsx`：

```tsx
interface VoiceStatusProps {
  isListening: boolean;
  isProcessing: boolean;
  confidence: number;
  error: string | null;
}

export default function VoiceStatus({
  isListening,
  isProcessing,
  confidence,
  error,
}: VoiceStatusProps) {
  if (error) {
    return (
      <div style={{
        padding: 'var(--space-2) var(--space-3)',
        background: '#FEE2E2',
        color: 'var(--color-error)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
      }}>
        ⚠️ {error}
      </div>
    );
  }

  if (isProcessing) {
    return (
      <div style={{
        padding: 'var(--space-2) var(--space-3)',
        background: 'var(--color-primary)',
        color: 'var(--color-text-inverse)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
      }}>
        <span style={{ animation: 'pulse 1.5s infinite' }}>⏳</span>
        正在处理...
      </div>
    );
  }

  if (isListening) {
    return (
      <div style={{
        padding: 'var(--space-2) var(--space-3)',
        background: '#FEE2E2',
        color: 'var(--color-error)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
      }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: 'var(--color-error)',
          animation: 'pulse 1s infinite',
        }} />
        正在录音... {confidence > 0 && `(${Math.round(confidence * 100)}%)`}
      </div>
    );
  }

  return null;
}
```

- [ ] **Step 4: 创建 VoiceButton**

创建 `frontend/src/features/voice/VoiceButton.tsx`：

```tsx
import { useState, useRef } from 'react';

interface VoiceButtonProps {
  isListening: boolean;
  isSupported: boolean;
  onToggle: () => void;
}

export default function VoiceButton({ isListening, isSupported, onToggle }: VoiceButtonProps) {
  const [isPressed, setIsPressed] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  if (!isSupported) {
    return (
      <button
        disabled
        title="您的浏览器不支持语音识别"
        style={{
          width: 48,
          height: 48,
          borderRadius: 'var(--radius-full)',
          background: 'var(--color-border)',
          color: 'var(--color-text-disabled)',
          fontSize: '1.2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'not-allowed',
          opacity: 0.5,
        }}
      >
        🎤
      </button>
    );
  }

  return (
    <button
      ref={buttonRef}
      onClick={onToggle}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      style={{
        width: 48,
        height: 48,
        borderRadius: 'var(--radius-full)',
        background: isListening
          ? 'var(--color-error)'
          : isPressed
          ? 'var(--color-primary-dark)'
          : 'var(--color-primary)',
        color: 'var(--color-text-inverse)',
        fontSize: '1.2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all var(--transition-fast)',
        transform: isPressed ? 'scale(0.95)' : 'scale(1)',
        boxShadow: isListening
          ? '0 0 0 4px rgba(234, 67, 53, 0.3)'
          : 'var(--shadow-md)',
        animation: isListening ? 'pulse 1.5s infinite' : 'none',
      }}
      aria-label={isListening ? '停止录音' : '开始语音'}
    >
      {isListening ? '⏹️' : '🎤'}
    </button>
  );
}
```

- [ ] **Step 5: 创建 VoicePanel**

创建 `frontend/src/features/voice/VoicePanel.tsx`：

```tsx
import { useState, useRef, useCallback } from 'react';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useVoiceStore } from '../../stores/useVoiceStore';
import VoiceButton from './VoiceButton';
import VoiceStatus from './VoiceStatus';
import WaveformVisualizer from './WaveformVisualizer';

export default function VoicePanel() {
  const {
    isListening,
    transcript,
    interimTranscript,
    confidence,
    isSupported,
    error: recognitionError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition();

  const { speak, isSpeaking } = useSpeechSynthesis();
  const { isProcessing, response, setProcessing, setResponse, reset } = useVoiceStore();

  const [isExpanded, setIsExpanded] = useState(false);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const handleToggle = useCallback(async () => {
    if (isListening) {
      stopListening();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setAudioStream(null);
      }

      const finalText = transcript + interimTranscript;
      if (finalText.trim()) {
        setProcessing(true);
        // TODO: Send to backend /api/voice/command
        // For now, simulate processing
        setTimeout(() => {
          setResponse(`已收到指令: "${finalText}"`);
          setProcessing(false);
          speak(`已收到指令: ${finalText}`);
        }, 1000);
      }
    } else {
      resetTranscript();
      setResponse(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        setAudioStream(stream);
      } catch {
        // Audio stream not available, still use speech recognition
      }

      startListening();
    }
  }, [
    isListening,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    resetTranscript,
    setProcessing,
    setResponse,
    speak,
  ]);

  const handleClose = () => {
    if (isListening) {
      stopListening();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      setAudioStream(null);
    }
    resetTranscript();
    setResponse(null);
    setIsExpanded(false);
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 'var(--space-6)',
        right: 'var(--space-6)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 'var(--space-3)',
      }}
    >
      {/* Expanded Panel */}
      {isExpanded && (
        <div
          style={{
            background: 'var(--color-surface)',
            borderRadius: 'var(--radius-xl)',
            boxShadow: 'var(--shadow-xl)',
            border: '1px solid var(--color-border)',
            padding: 'var(--space-4)',
            width: '320px',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>
              🎙️ 语音助手
            </span>
            <button
              onClick={handleClose}
              style={{
                background: 'transparent',
                padding: 'var(--space-1)',
                fontSize: 'var(--font-size-lg)',
              }}
            >
              ✕
            </button>
          </div>

          {/* Waveform */}
          <WaveformVisualizer stream={audioStream} isActive={isListening} />

          {/* Status */}
          <VoiceStatus
            isListening={isListening}
            isProcessing={isProcessing}
            confidence={confidence}
            error={recognitionError}
          />

          {/* Transcript Display */}
          <div
            style={{
              minHeight: '60px',
              padding: 'var(--space-3)',
              background: 'var(--color-bg-secondary)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text)',
            }}
          >
            {transcript || interimTranscript ? (
              <>
                <span>{transcript}</span>
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  {interimTranscript}
                </span>
              </>
            ) : (
              <span style={{ color: 'var(--color-text-disabled)' }}>
                {isListening ? '请说话...' : '点击麦克风开始语音指令'}
              </span>
            )}
          </div>

          {/* Response */}
          {response && (
            <div
              style={{
                padding: 'var(--space-3)',
                background: 'rgba(52, 168, 83, 0.1)',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-accent)',
              }}
            >
              💬 {response}
            </div>
          )}

          {/* Tips */}
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
            💡 试试说: "帮我创建明天下午3点的会议"
          </div>
        </div>
      )}

      {/* Voice Button */}
      <VoiceButton
        isListening={isListening}
        isSupported={isSupported}
        onToggle={() => {
          if (!isExpanded) {
            setIsExpanded(true);
          } else {
            handleToggle();
          }
        }}
      />
    </div>
  );
}
```

- [ ] **Step 6: 运行测试确认通过 (GREEN)**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run src/features/voice/__tests__/VoiceButton.test.tsx
```

Expected: `5 passed`

- [ ] **Step 7: 添加脉冲动画到全局样式**

在 `frontend/src/styles/global.css` 末尾添加：

```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
```

- [ ] **Step 8: 提交**

```bash
git add frontend/
git commit -m "feat: add VoiceButton, VoicePanel, WaveformVisualizer, and VoiceStatus components"
```

---

## Task 7: 集成语音面板到日历页面

**Files:**
- Modify: `frontend/src/features/calendar/CalendarPage.tsx`

- [ ] **Step 1: 添加 VoicePanel 到 CalendarPage**

修改 `frontend/src/features/calendar/CalendarPage.tsx`，在文件顶部添加导入：

```tsx
import VoicePanel from '../voice/VoicePanel';
```

在 `</div>` 结束标签前（`</div>` 的最后一行之前）添加：

```tsx
<VoicePanel />
```

- [ ] **Step 2: 运行全部前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add frontend/
git commit -m "feat: integrate VoicePanel into calendar page"
```

---

## Task 8: 完整验证

- [ ] **Step 1: 后端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/backend
pytest -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 2: 前端测试**

```bash
cd /Users/linchengda/Desktop/vocal-calendar/frontend
npx vitest run
```

Expected: 所有测试通过

- [ ] **Step 3: 手动验证**

1. 登录 → 日历页面右下角出现语音按钮
2. 点击语音按钮 → 展开语音面板
3. 再次点击 → 开始录音 → 波形显示
4. 说话 → 实时转文字显示
5. 停止 → 处理中状态 → 显示响应
6. 浏览器不支持时 → 按钮灰化 + 提示

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "chore: phase 5 complete — voice interaction with Web Speech API"
```

---

## 阶段交付物清单

| 交付物 | 状态 |
|--------|------|
| useSpeechRecognition Hook | ☐ |
| useSpeechSynthesis Hook | ☐ |
| useAudioVisualizer Hook | ☐ |
| useVoiceStore | ☐ |
| WaveformVisualizer 组件 | ☐ |
| VoiceButton 组件 | ☐ |
| VoicePanel 组件 | ☐ |
| VoiceStatus 组件 | ☐ |
| 日历页面集成 | ☐ |
