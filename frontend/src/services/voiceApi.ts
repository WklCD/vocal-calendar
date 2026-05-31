import api from './api';

interface VoiceCommandResponse {
  intent: string;
  entities: Record<string, any>;
  confidence: number;
  need_clarify: boolean;
  clarify_question: string | null;
  response_text: string;
}

export const voiceApi = {
  sendCommand: (text: string) =>
    api.post<{ code: number; data: VoiceCommandResponse; message: string }>(
      '/voice/command',
      { text }
    ),

  getLogs: () =>
    api.get<{ code: number; data: any[]; message: string }>('/voice/logs'),

  getHelp: () =>
    api.get<{ code: number; data: any[]; message: string }>('/voice/help'),
};
