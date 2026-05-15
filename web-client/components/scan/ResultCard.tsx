'use client';

import Link from 'next/link';
import type { ReadResponse } from '@/lib/types';
import LinesSummary from './LinesSummary';
import ProtocolPanel from './ProtocolPanel';

interface Props {
  result: ReadResponse;
  onAskQuestion: () => void;
  onScanAnother: () => void;
  onBack: () => void;
}

const outcomeConfig: Record<string, { bg: string; label: string; icon: string }> = {
  positive: { bg: '#dc2626', label: 'Positive', icon: '+' },
  negative: { bg: '#16a34a', label: 'Negative', icon: '–' },
  invalid:  { bg: '#d97706', label: 'Invalid',  icon: '?' },
};

export default function ResultCard({ result, onAskQuestion, onScanAnother, onBack }: Props) {
  const { result: r, cassette_type } = result;
  const conf = Math.round(r.confidence * 100);
  const cfg = outcomeConfig[r.outcome] ?? { bg: '#6b7280', label: 'Unknown', icon: '?' };
  const typeLabel = cassette_type.charAt(0).toUpperCase() + cassette_type.slice(1);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#f7f8fc' }}>

      {/* Outcome banner */}
      <div className="relative px-5 pt-12 pb-10" style={{ backgroundColor: cfg.bg }}>
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm font-medium mb-8"
          style={{ color: 'rgba(255,255,255,0.65)' }}
        >
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
            <path d="M19 12H5M5 12l7-7M5 12l7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Back
        </button>

        <div className="flex items-end justify-between">
          <div>
            <p className="text-white/70 text-sm font-medium uppercase tracking-widest mb-1">
              {typeLabel} RDT
            </p>
            <p className="text-white text-5xl font-bold leading-none">{cfg.label}</p>
            {r.invalid_reason && (
              <p className="text-white/70 text-sm mt-2 capitalize">
                {r.invalid_reason.replace(/_/g, ' ')}
              </p>
            )}
          </div>
          {/* Big icon */}
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl font-bold text-white mb-1"
            style={{ backgroundColor: 'rgba(255,255,255,0.18)' }}
          >
            {cfg.icon}
          </div>
        </div>

        {/* Confidence bar */}
        <div className="mt-6">
          <div className="flex justify-between text-xs text-white/60 mb-1.5">
            <span>Confidence</span>
            <span>{conf}%</span>
          </div>
          <div className="h-1.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}>
            <div
              className="h-full rounded-full bg-white transition-all"
              style={{ width: `${conf}%` }}
            />
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-5 space-y-3 overflow-y-auto pb-24">

        {/* AI observation */}
        <div className="bg-white rounded-2xl p-4" style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            What the AI saw
          </p>
          <LinesSummary lines={r.lines} />
        </div>

        {/* Explanation */}
        <div className="bg-white rounded-2xl p-4" style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Explanation
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">{r.explanation}</p>
        </div>

        {/* Protocol */}
        {result.protocol && <ProtocolPanel protocol={result.protocol} />}

        {/* Actions */}
        <div className="pt-1 space-y-2.5">
          <button
            onClick={onAskQuestion}
            className="w-full text-white py-4 rounded-2xl text-sm font-semibold flex items-center justify-center gap-2 transition-opacity active:opacity-80"
            style={{ backgroundColor: '#0a1e46' }}
          >
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
              <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Ask a question
          </button>
          <button
            onClick={onScanAnother}
            className="w-full py-4 rounded-2xl text-sm font-semibold text-gray-600 bg-white transition-opacity active:opacity-80"
            style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}
          >
            Scan another
          </button>
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-gray-400 pt-2 pb-4">
          Not a medical device · Always consult a clinician
        </p>
      </div>
    </div>
  );
}
