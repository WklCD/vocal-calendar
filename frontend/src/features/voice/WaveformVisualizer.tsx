import { useEffect } from 'react';
import { useAudioVisualizer } from '../../hooks/useAudioVisualizer';

interface WaveformVisualizerProps {
  stream: MediaStream | null;
  isActive: boolean;
}

export default function WaveformVisualizer({ stream, isActive }: WaveformVisualizerProps) {
  const { canvasRef, startVisualization, stopVisualization } = useAudioVisualizer();

  useEffect(() => {
    if (isActive && stream) {
      startVisualization(stream);
    } else {
      stopVisualization();
    }
  }, [isActive, stream, startVisualization, stopVisualization]);

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={60}
      style={{
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        width: '100%',
        height: '60px',
        opacity: isActive ? 1 : 0.3,
        transition: 'opacity var(--transition-normal)',
      }}
    />
  );
}
