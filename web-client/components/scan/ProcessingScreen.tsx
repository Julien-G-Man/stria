'use client';

import { useState, useEffect } from 'react';

const stepLabels = ['Detecting cassette', 'Analyzing lines', 'Checking protocols'];

interface Props {
  backgroundUrl: string;
}

export default function ProcessingScreen({ backgroundUrl }: Props) {
  const [labelIndex, setLabelIndex] = useState(0);
  const [showSlow, setShowSlow] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => setLabelIndex((i) => (i + 1) % stepLabels.length), 1300);
    const slow = setTimeout(() => setShowSlow(true), 8000);
    return () => { clearInterval(interval); clearTimeout(slow); };
  }, []);

  return (
    <div className="fixed inset-0 z-40 flex flex-col items-center justify-center overflow-hidden">
      {/* Blurred photo background */}
      <div
        className="absolute inset-0 bg-cover bg-center scale-110"
        style={{ backgroundImage: `url(${backgroundUrl})`, filter: 'blur(18px) brightness(0.35)' }}
      />

      {/* Dark scrim */}
      <div className="absolute inset-0" style={{ backgroundColor: 'rgba(4,8,18,0.5)' }} />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-7 px-8 w-full max-w-xs text-center">
        {/* Logo pulse */}
        <p className="font-bold text-2xl tracking-[0.25em] text-white animate-pulse">
          STRIA
        </p>

        {/* Spinner ring */}
        <div
          className="w-16 h-16 rounded-full border-4 animate-spin"
          style={{
            borderColor: 'rgba(255,255,255,0.15)',
            borderTopColor: '#60a5fa',
          }}
        />

        <div className="space-y-2">
          <p className="text-white text-base font-medium">Reading test…</p>
          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>
            {stepLabels[labelIndex]}
          </p>
          {showSlow && (
            <p className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Taking a moment…
            </p>
          )}
        </div>

        {/* Progress bar */}
        <div className="w-full rounded-full overflow-hidden h-1" style={{ backgroundColor: 'rgba(255,255,255,0.12)' }}>
          <div
            className="h-full rounded-full"
            style={{
              backgroundColor: '#60a5fa',
              animation: 'stria-progress 4s ease-in-out forwards',
            }}
          />
        </div>
      </div>

      <style>{`
        @keyframes stria-progress { from { width: 0% } to { width: 92% } }
      `}</style>
    </div>
  );
}
