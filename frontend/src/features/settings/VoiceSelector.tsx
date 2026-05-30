import { useState } from 'react';
import { MIMO_VOICES, ttsApi } from '../../services/ttsApi';
import { useTtsStore } from '../../stores/useTtsStore';

const SAMPLE_TEXTS: Record<string, string> = {
  zh: '你好，我是你的语音助手，很高兴为你服务。',
  en: 'Hello, I am your voice assistant. Nice to meet you.',
};

export default function VoiceSelector() {
  const { voice, setVoice } = useTtsStore();
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null);

  const zhVoices = MIMO_VOICES.filter((v) => v.lang === 'zh');
  const enVoices = MIMO_VOICES.filter((v) => v.lang === 'en');

  const handlePreview = async (voiceId: string) => {
    if (previewingVoice) {
      ttsApi.stopAudio();
      setPreviewingVoice(null);
      return;
    }

    const voiceInfo = MIMO_VOICES.find((v) => v.id === voiceId);
    const sampleText = voiceInfo?.lang === 'en' ? SAMPLE_TEXTS.en : SAMPLE_TEXTS.zh;

    try {
      setPreviewingVoice(voiceId);
      const audioBase64 = await ttsApi.synthesize(sampleText, voiceId);
      await ttsApi.playAudio(audioBase64);
    } catch (error) {
      console.error('Voice preview failed:', error);
    } finally {
      setPreviewingVoice(null);
    }
  };

  const renderVoiceGroup = (title: string, voices: typeof MIMO_VOICES) => (
    <div style={{ marginBottom: 'var(--space-4)' }}>
      <h4 style={{
        fontSize: 'var(--font-size-sm)',
        fontWeight: 600,
        color: 'var(--color-text-secondary)',
        marginBottom: 'var(--space-2)',
        padding: '0 var(--space-2)',
      }}>
        {title}
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
        {voices.map((v) => (
          <div
            key={v.id}
            onClick={() => setVoice(v.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: 'var(--space-3) var(--space-4)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              background: voice === v.id ? 'var(--color-primary)' : 'transparent',
              color: voice === v.id ? 'var(--color-text-inverse)' : 'var(--color-text)',
              transition: 'var(--transition-fast)',
            }}
            onMouseEnter={(e) => {
              if (voice !== v.id) {
                e.currentTarget.style.background = 'var(--color-surface-hover)';
              }
            }}
            onMouseLeave={(e) => {
              if (voice !== v.id) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <span style={{ fontWeight: 500 }}>{v.name}</span>
              <span style={{
                fontSize: 'var(--font-size-xs)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                background: voice === v.id ? 'rgba(255,255,255,0.2)' : 'var(--color-bg-secondary)',
                color: voice === v.id ? 'var(--color-text-inverse)' : 'var(--color-text-secondary)',
              }}>
                {v.gender}
              </span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePreview(v.id);
              }}
              style={{
                padding: 'var(--space-1) var(--space-3)',
                borderRadius: 'var(--radius-sm)',
                background: voice === v.id ? 'rgba(255,255,255,0.2)' : 'var(--color-primary)',
                color: 'var(--color-text-inverse)',
                fontSize: 'var(--font-size-xs)',
                fontWeight: 500,
              }}
            >
              {previewingVoice === v.id ? '停止' : '试听'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div style={{ padding: 'var(--space-4)' }}>
      <h3 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: 600,
        marginBottom: 'var(--space-4)',
        color: 'var(--color-text)',
      }}>
        音色选择
      </h3>
      {renderVoiceGroup('中文', zhVoices)}
      {renderVoiceGroup('English', enVoices)}
    </div>
  );
}
