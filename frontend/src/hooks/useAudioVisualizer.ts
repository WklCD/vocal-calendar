import { useRef, useCallback, useEffect, useState } from 'react';

interface UseAudioVisualizerReturn {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  startVisualization: (stream: MediaStream) => void;
  stopVisualization: () => void;
  isActive: boolean;
}

export function useAudioVisualizer(): UseAudioVisualizerReturn {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const [isActive, setIsActive] = useState(false);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);

    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--color-bg-secondary').trim() || '#F8F9FA';
    ctx.fillRect(0, 0, width, height);

    ctx.lineWidth = 2;
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, '#4285F4');
    gradient.addColorStop(0.5, '#34A853');
    gradient.addColorStop(1, '#EA4335');
    ctx.strokeStyle = gradient;

    ctx.beginPath();
    const sliceWidth = width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * height) / 2;
      if (i === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
      x += sliceWidth;
    }

    ctx.lineTo(width, height / 2);
    ctx.stroke();
    animationFrameRef.current = requestAnimationFrame(draw);
  }, []);

  const startVisualization = useCallback((stream: MediaStream) => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      setIsActive(true);
      draw();
    } catch (e) {
      console.error('Failed to start audio visualization:', e);
    }
  }, [draw]);

  const stopVisualization = useCallback(() => {
    if (animationFrameRef.current) { cancelAnimationFrame(animationFrameRef.current); }
    if (audioContextRef.current) { audioContextRef.current.close(); audioContextRef.current = null; }
    analyserRef.current = null;
    setIsActive(false);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) { ctx.clearRect(0, 0, canvas.width, canvas.height); }
    }
  }, []);

  useEffect(() => { return () => { stopVisualization(); }; }, [stopVisualization]);

  return { canvasRef, startVisualization, stopVisualization, isActive };
}
