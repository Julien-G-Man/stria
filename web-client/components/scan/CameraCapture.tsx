'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import LightboxTip from './LightboxTip';
import { detectCassette } from '@/lib/api';
import type { CassetteType } from '@/lib/types';

type DetectionState = 'none' | 'detected' | 'stable' | 'error';

const STABILITY_MS = 1500;
const POLL_INTERVAL_MS = 1500;

const typeLabels: Record<CassetteType, string> = {
  malaria: 'Malaria RDT',
  covid: 'COVID-19 RDT',
  pregnancy: 'Pregnancy Test',
  hiv: 'HIV RDT',
};

const frameColors: Record<DetectionState, string> = {
  none: 'rgba(255,255,255,0.75)',
  detected: '#60a5fa',
  stable: '#4ade80',
  error: '#f87171',
};

const instructions: Record<DetectionState, string> = {
  none: 'Place cassette in the frame',
  detected: 'Hold steady…',
  stable: 'Capturing…',
  error: 'Camera access denied',
};

interface Props {
  cassetteType: CassetteType;
  onCapture: (blob: Blob, dataUrl: string) => void;
  onBack: () => void;
  errorMessage?: string | null;
}

function CornerBracket({
  top, left, color,
}: {
  top: boolean; left: boolean; color: string;
}) {
  return (
    <div
      className="absolute w-8 h-8 transition-colors duration-300"
      style={{
        top: top ? 0 : 'auto',
        bottom: top ? 'auto' : 0,
        left: left ? 0 : 'auto',
        right: left ? 'auto' : 0,
        borderTop: top ? `3px solid ${color}` : 'none',
        borderBottom: top ? 'none' : `3px solid ${color}`,
        borderLeft: left ? `3px solid ${color}` : 'none',
        borderRight: left ? 'none' : `3px solid ${color}`,
        borderRadius: top && left ? '4px 0 0 0' : top ? '0 4px 0 0' : left ? '0 0 0 4px' : '0 0 4px 0',
      }}
    />
  );
}

export default function CameraCapture({ cassetteType, onCapture, onBack, errorMessage }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stableTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const capturedRef = useRef(false);
  const detectingRef = useRef(false);

  const [detectionState, setDetectionState] = useState<DetectionState>('none');
  const [showLightbox, setShowLightbox] = useState(false);
  const [streamReady, setStreamReady] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  useEffect(() => {
    if (!localStorage.getItem('stria_lightbox_dismissed')) setShowLightbox(true);
  }, []);

  useEffect(() => {
    let stream: MediaStream | null = null;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'environment' } })
      .then((s) => {
        stream = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          videoRef.current.onloadedmetadata = () => setStreamReady(true);
        }
      })
      .catch(() => setDetectionState('error'));
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, []);

  const captureAndSubmit = useCallback(() => {
    if (capturedRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    capturedRef.current = true;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    canvas.toBlob((blob) => { if (blob) onCapture(blob, dataUrl); }, 'image/jpeg', 0.9);
  }, [onCapture]);

  useEffect(() => {
    if (!streamReady) return;
    const pollCanvas = document.createElement('canvas');
    pollRef.current = setInterval(() => {
      const video = videoRef.current;
      if (!video || capturedRef.current) return;
      const w = 320;
      const h = Math.round((video.videoHeight * w) / video.videoWidth) || 240;
      pollCanvas.width = w;
      pollCanvas.height = h;
      pollCanvas.getContext('2d')?.drawImage(video, 0, 0, w, h);
      pollCanvas.toBlob(async (blob) => {
        if (!blob || capturedRef.current || detectingRef.current) return;
        detectingRef.current = true;
        try {
          const { detected } = await detectCassette(blob);
          if (capturedRef.current) return;
          if (detected) {
            setDetectionState((prev) => {
              if (prev === 'stable') return 'stable';
              if (prev !== 'detected') {
                stableTimerRef.current = setTimeout(() => {
                  setDetectionState('stable');
                  captureAndSubmit();
                }, STABILITY_MS);
              }
              return 'detected';
            });
          } else {
            if (stableTimerRef.current) { clearTimeout(stableTimerRef.current); stableTimerRef.current = null; }
            setDetectionState((prev) => (prev === 'stable' ? 'stable' : 'none'));
          }
        } catch { /* ignore polling errors */ }
        finally { detectingRef.current = false; }
      }, 'image/jpeg', 0.6);
    }, POLL_INTERVAL_MS);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (stableTimerRef.current) clearTimeout(stableTimerRef.current);
    };
  }, [streamReady, captureAndSubmit]);

  const frameColor = frameColors[detectionState];
  const instructionText = errorMessage ?? instructions[detectionState];
  const frameStyle = isMobile
    ? { width: '70%', aspectRatio: '3/5' }
    : { width: '80%', aspectRatio: '5/3' };

  return (
    <div className="fixed inset-0 bg-black">
      {/* Full-screen video */}
      <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />

      {/* Vignette */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at 50% 45%, transparent 38%, rgba(0,0,0,0.55) 100%)',
      }} />

      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 pt-12 pb-4">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full flex items-center justify-center"
          style={{ backgroundColor: 'rgba(0,0,0,0.35)', backdropFilter: 'blur(6px)' }}
          aria-label="Back"
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24">
            <path d="M19 12H5M5 12l7-7M5 12l7 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <div className="px-4 py-1.5 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.35)', backdropFilter: 'blur(6px)' }}>
          <span className="text-white text-sm font-semibold">{typeLabels[cassetteType]}</span>
        </div>

        <button
          onClick={() => setShowLightbox(true)}
          className="w-10 h-10 rounded-full flex items-center justify-center text-base"
          style={{ backgroundColor: 'rgba(0,0,0,0.35)', backdropFilter: 'blur(6px)' }}
          aria-label="Lighting tip"
        >
          ⚡
        </button>
      </div>

      {/* Guide frame — portrait on mobile, landscape on desktop */}
      <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
        <div className="relative" style={frameStyle}>
          <CornerBracket top left color={frameColor} />
          <CornerBracket top={true} left={false} color={frameColor} />
          <CornerBracket top={false} left color={frameColor} />
          <CornerBracket top={false} left={false} color={frameColor} />

          {/* Stable pulse ring */}
          {detectionState === 'stable' && (
            <div className="absolute inset-0 rounded-sm animate-ping opacity-20" style={{ border: `2px solid ${frameColor}` }} />
          )}
        </div>
      </div>

      {/* Instruction pill */}
      <div className="absolute z-10 left-0 right-0 flex justify-center" style={{ bottom: '160px' }}>
        <div className="px-5 py-2.5 rounded-full" style={{ backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(8px)' }}>
          <p className="text-white text-sm font-medium">{instructionText}</p>
        </div>
      </div>

      {/* Bottom controls */}
      <div className="absolute bottom-0 left-0 right-0 z-10 flex flex-col items-center pb-12 pt-6 gap-5"
        style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%)' }}
      >
        {/* Shutter button */}
        <button
          onClick={captureAndSubmit}
          className="w-20 h-20 rounded-full flex items-center justify-center transition-transform active:scale-95"
          style={{ border: '3px solid rgba(255,255,255,0.9)' }}
          aria-label="Capture photo"
        >
          <div className="w-[60px] h-[60px] rounded-full bg-white" />
        </button>

        <p className="text-xs" style={{ color: 'rgba(255,255,255,0.45)' }}>
          Tap to capture manually
        </p>
      </div>

      <canvas ref={canvasRef} className="hidden" />
      {showLightbox && <LightboxTip onDismiss={() => setShowLightbox(false)} />}
    </div>
  );
}
