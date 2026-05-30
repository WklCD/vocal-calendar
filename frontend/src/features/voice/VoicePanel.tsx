import { useState, useRef, useCallback } from 'react';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useVoiceStore } from '../../stores/useVoiceStore';
import VoiceButton from './VoiceButton';
import VoiceStatus from './VoiceStatus';
import WaveformVisualizer from './WaveformVisualizer';

export default function VoicePanel() {
  const { isListening, transcript, interimTranscript, confidence, isSupported, error: recognitionError, startListening, stopListening, resetTranscript } = useSpeechRecognition();
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
      } catch { }
      startListening();
    }
  }, [isListening, transcript, interimTranscript, startListening, stopListening, resetTranscript, setProcessing, setResponse, speak]);

  const handleClose = () => {
    if (isListening) { stopListening(); }
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
    <div style={{ position: 'fixed', bottom: 'var(--space-6)', right: 'var(--space-6)', zIndex: 100, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 'var(--space-3)' }}>
      {isExpanded && (
        <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-xl)', boxShadow: 'var(--shadow-xl)', border: '1px solid var(--color-border)', padding: 'var(--space-4)', width: '320px', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>🎙️ 语音助手</span>
            <button onClick={handleClose} style={{ background: 'transparent', padding: 'var(--space-1)', fontSize: 'var(--font-size-lg)' }}>✕</button>
          </div>
          <WaveformVisualizer stream={audioStream} isActive={isListening} />
          <VoiceStatus isListening={isListening} isProcessing={isProcessing} confidence={confidence} error={recognitionError} />
          <div style={{ minHeight: '60px', padding: 'var(--space-3)', background: 'var(--color-bg-secondary)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text)' }}>
            {transcript || interimTranscript ? (
              <><span>{transcript}</span><span style={{ color: 'var(--color-text-secondary)' }}>{interimTranscript}</span></>
            ) : (
              <span style={{ color: 'var(--color-text-disabled)' }}>{isListening ? '请说话...' : '点击麦克风开始语音指令'}</span>
            )}
          </div>
          {response && (
            <div style={{ padding: 'var(--space-3)', background: 'rgba(52, 168, 83, 0.1)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', color: 'var(--color-accent)' }}>💬 {response}</div>
          )}
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>💡 试试说: "帮我创建明天下午3点的会议"</div>
        </div>
      )}
      <VoiceButton isListening={isListening} isSupported={isSupported} onToggle={() => { if (!isExpanded) { setIsExpanded(true); } else { handleToggle(); } }} />
    </div>
  );
}
