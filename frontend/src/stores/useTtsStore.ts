import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TtsState {
  voice: string;
  setVoice: (voice: string) => void;
}

export const useTtsStore = create<TtsState>()(
  persist(
    (set) => ({
      voice: 'mimo_default',
      setVoice: (voice) => set({ voice }),
    }),
    {
      name: 'tts-storage',
    }
  )
);
