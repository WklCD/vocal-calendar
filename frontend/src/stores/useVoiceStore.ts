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
  session: { lastIntent: null, lastEntities: null, turnCount: 0 },

  setRecording: (recording) => set({ isRecording: recording }),
  setTranscript: (text) => set({ transcript: text }),
  setInterimTranscript: (text) => set({ interimTranscript: text }),
  setConfidence: (confidence) => set({ confidence }),
  setProcessing: (processing) => set({ isProcessing: processing }),
  setResponse: (response) => set({ response }),
  updateSession: (intent, entities) => set((state) => ({ session: { lastIntent: intent, lastEntities: entities, turnCount: state.session.turnCount + 1 } })),
  clearSession: () => set({ session: { lastIntent: null, lastEntities: null, turnCount: 0 } }),
  reset: () => set({ isRecording: false, transcript: '', interimTranscript: '', confidence: 0, isProcessing: false, response: null }),
}));
