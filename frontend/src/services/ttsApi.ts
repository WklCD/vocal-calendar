import api from './api';

export interface MiMoVoice {
  id: string;
  name: string;
  lang: string;
  gender: string;
}

export const MIMO_VOICES: MiMoVoice[] = [
  { id: 'mimo_default', name: 'MiMo默认', lang: 'zh', gender: '女' },
  { id: '冰糖', name: '冰糖', lang: 'zh', gender: '女' },
  { id: '茉莉', name: '茉莉', lang: 'zh', gender: '女' },
  { id: '苏打', name: '苏打', lang: 'zh', gender: '男' },
  { id: '白桦', name: '白桦', lang: 'zh', gender: '男' },
  { id: 'Mia', name: 'Mia', lang: 'en', gender: '女' },
  { id: 'Chloe', name: 'Chloe', lang: 'en', gender: '女' },
  { id: 'Milo', name: 'Milo', lang: 'en', gender: '男' },
  { id: 'Dean', name: 'Dean', lang: 'en', gender: '男' },
];

let currentAudio: HTMLAudioElement | null = null;
let currentAbortController: AbortController | null = null;
let requestCounter = 0;

export const ttsApi = {
  async synthesize(text: string, voice: string = 'mimo_default'): Promise<string> {
    // 取消之前的请求
    if (currentAbortController) {
      currentAbortController.abort();
    }
    currentAbortController = new AbortController();
    const myRequest = ++requestCounter;

    try {
      const resp = await api.post('/ai/tts', { text, voice }, {
        signal: currentAbortController.signal,
        timeout: 60000, // 60秒超时
      });

      // 检查是否已被更新的请求取代
      if (myRequest !== requestCounter) {
        return ''; // 静默丢弃过期结果
      }

      return resp.data.data.audio;
    } catch (err: any) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') {
        return ''; // 请求被取消
      }
      throw err;
    }
  },

  playAudio(base64Data: string): Promise<void> {
    return new Promise((resolve) => {
      if (!base64Data) {
        resolve();
        return;
      }
      this.stopAudio();
      const audio = new Audio(`data:audio/wav;base64,${base64Data}`);
      currentAudio = audio;

      audio.onended = () => {
        if (currentAudio === audio) currentAudio = null;
        resolve();
      };
      audio.onerror = () => {
        if (currentAudio === audio) currentAudio = null;
        resolve();
      };
      audio.play().catch(() => {
        if (currentAudio === audio) currentAudio = null;
        resolve();
      });
    });
  },

  stopAudio(): void {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio.src = '';
      currentAudio = null;
    }
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }
    requestCounter++; // 使所有进行中的请求结果失效
  },

  get isPlaying(): boolean {
    return currentAudio !== null && !currentAudio.paused;
  },
};
