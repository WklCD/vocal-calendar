import { useState, useEffect, useRef, useCallback } from 'react';

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

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const transcriptRef = useRef('');
  const isActiveRef = useRef(false);

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
      isActiveRef.current = true;
      setIsListening(true);
      setError(null);
    };

    recognition.onresult = (event: any) => {
      let finalText = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
          setConfidence(result[0].confidence);
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalText) {
        transcriptRef.current += finalText;
        setTranscript(transcriptRef.current);
      }
      setInterimTranscript(interim);
    };

    recognition.onerror = (event: any) => {
      if (event.error !== 'aborted' && event.error !== 'no-speech') {
        setError(`语音识别错误: ${event.error}`);
      }
      isActiveRef.current = false;
      setIsListening(false);
    };

    recognition.onend = () => {
      isActiveRef.current = false;
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {}
      isActiveRef.current = false;
    };
  }, [SpeechRecognition]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;

    // Reset transcript
    transcriptRef.current = '';
    setTranscript('');
    setInterimTranscript('');
    setConfidence(0);
    setError(null);

    // Abort any existing session, then start fresh
    if (isActiveRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      isActiveRef.current = false;
    }

    try {
      recognitionRef.current.start();
    } catch (e) {
      // If start fails, try once more after abort
      try {
        recognitionRef.current.abort();
        recognitionRef.current.start();
      } catch {}
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {}
    isActiveRef.current = false;
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    transcriptRef.current = '';
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
