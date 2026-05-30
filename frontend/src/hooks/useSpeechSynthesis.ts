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
  const speakingRef = useRef(false);

  const isSupported = true;

  const speak = useCallback(async (text: string) => {
    if (speakingRef.current) {
      ttsApi.stopAudio();
    }

    try {
      speakingRef.current = true;
      setIsSpeaking(true);

      const audioBase64 = await ttsApi.synthesize(text, voice);
      await ttsApi.playAudio(audioBase64);
    } catch (error) {
      console.error('TTS synthesis failed:', error);
    } finally {
      speakingRef.current = false;
      setIsSpeaking(false);
    }
  }, [voice]);

  const stop = useCallback(() => {
    ttsApi.stopAudio();
    speakingRef.current = false;
    setIsSpeaking(false);
  }, []);

  return { speak, stop, isSpeaking, isSupported };
}
