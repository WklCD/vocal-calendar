import api from './api';

export interface MiMoVoice {
  id: string;
  name: string;
  lang: string;
  gender: string;
}

export const MIMO_VOICES: MiMoVoice[] = [
  { id: 'mimo_default', name: 'MiMo默认', lang: 'zh', gender: '女' },
  { id: 'yueyue', name: '悦悦', lang: 'zh', gender: '女' },
  { id: 'tiantian', name: '甜甜', lang: 'zh', gender: '女' },
  { id: 'achen', name: '阿辰', lang: 'zh', gender: '男' },
  { id: 'alin', name: '阿林', lang: 'zh', gender: '男' },
  { id: 'Mia', name: 'Mia', lang: 'en', gender: '女' },
  { id: 'Chloe', name: 'Chloe', lang: 'en', gender: '女' },
  { id: 'Milo', name: 'Milo', lang: 'en', gender: '男' },
  { id: 'Dean', name: 'Dean', lang: 'en', gender: '男' },
];

let currentAudio: HTMLAudioElement | null = null;

export const ttsApi = {
  async synthesize(text: string, voice: string = 'mimo_default'): Promise<string> {
    const resp = await api.post('/ai/tts', { text, voice });
    return resp.data.data.audio;
  },

  playAudio(base64Data: string): Promise<void> {
    return new Promise((resolve) => {
      this.stopAudio();
      const audio = new Audio(`data:audio/wav;base64,${base64Data}`);
      currentAudio = audio;
      audio.onended = () => {
        currentAudio = null;
        resolve();
      };
      audio.onerror = () => {
        currentAudio = null;
        resolve();
      };
      audio.play();
    });
  },

  stopAudio(): void {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
  },

  get isPlaying(): boolean {
    return currentAudio !== null && !currentAudio.paused;
  },
};
