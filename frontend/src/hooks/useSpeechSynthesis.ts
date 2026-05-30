import { useState, useCallback, useRef } from 'react';
import { ttsApi } from '../services/ttsApi';
import { useTtsStore } from '../stores/useTtsStore';

interface UseSpeechSynthesisReturn {
  speak: (text: string) => Promise<void>;
  stop: () => void;
  isSpeaking: boolean;
  isSupported: boolean;
}

export function useSpeechSynthesis(): UseSpeechSynthesisReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const { voice } = useTtsStore();
  const activeRef = useRef(false);
  const seqRef = useRef(0);

  const isSupported = true;

  const speak = useCallback(async (text: string) => {
    // 停止当前播放
    ttsApi.stopAudio();

    const mySeq = ++seqRef.current;
    activeRef.current = true;
    setIsSpeaking(true);

    try {
      const audioBase64 = await ttsApi.synthesize(text, voice);

      // 检查是否被更新的调用取代
      if (mySeq !== seqRef.current || !activeRef.current) {
        return;
      }

      if (audioBase64) {
        await ttsApi.playAudio(audioBase64);
      }
    } catch (error) {
      console.error('TTS failed:', error);
    } finally {
      // 只有当前调用才清除状态
      if (mySeq === seqRef.current) {
        activeRef.current = false;
        setIsSpeaking(false);
      }
    }
  }, [voice]);

  const stop = useCallback(() => {
    activeRef.current = false;
    ttsApi.stopAudio();
    setIsSpeaking(false);
  }, []);

  return { speak, stop, isSpeaking, isSupported };
}
