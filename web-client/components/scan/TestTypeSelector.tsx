'use client';

import Link from 'next/link';
import type { CassetteType } from '@/lib/types';

interface TypeCard {
  type: CassetteType;
  emoji: string;
  name: string;
  description: string;
  accent: string;
}

const types: TypeCard[] = [
  {
    type: 'malaria',
    emoji: '🦟',
    name: 'Malaria',
    description: 'Plasmodium falciparum · HRP2/pLDH',
    accent: '#e53e3e',
  },
  {
    type: 'covid',
    emoji: '🦠',
    name: 'COVID-19',
    description: 'SARS-CoV-2 antigen rapid test',
    accent: '#3182ce',
  },
  {
    type: 'pregnancy',
    emoji: '🤰',
    name: 'Pregnancy',
    description: 'hCG hormone detection strip',
    accent: '#d53f8c',
  },
  {
    type: 'hiv',
    emoji: '🩸',
    name: 'HIV',
    description: 'HIV-1/2 antibody detection',
    accent: '#dd6b20',
  },
];

interface Props {
  onSelect: (type: CassetteType) => void;
}

export default function TestTypeSelector({ onSelect }: Props) {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#f7f8fc' }}>
      {/* Dark header */}
      <div className="px-5 pt-12 pb-20" style={{ backgroundColor: '#0a1e46' }}>
        <Link
          href="/"
          className="text-sm font-medium flex items-center gap-1.5"
          style={{ color: 'rgba(255,255,255,0.5)' }}
        >
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
            <path d="M19 12H5M5 12l7-7M5 12l7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          STRIA
        </Link>
        <h1 className="text-white text-3xl font-bold mt-6 leading-snug">
          What type of test?
        </h1>
        <p className="mt-2 text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>
          Select the cassette type to begin
        </p>
      </div>

      {/* Card list — overlaps the header */}
      <div className="flex-1 px-4 -mt-10 pb-10 space-y-3">
        {types.map((t) => (
          <button
            key={t.type}
            onClick={() => onSelect(t.type)}
            className="w-full bg-white rounded-2xl p-4 flex items-center gap-4 text-left transition-all active:scale-[0.98]"
            style={{ boxShadow: '0 2px 12px rgba(0,0,0,0.07)' }}
          >
            {/* Accent icon box */}
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0"
              style={{ backgroundColor: `${t.accent}18` }}
            >
              {t.emoji}
            </div>

            {/* Text */}
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900 text-base">{t.name}</p>
              <p className="text-xs text-gray-400 mt-0.5 truncate">{t.description}</p>
            </div>

            {/* Arrow */}
            <svg
              width="18"
              height="18"
              fill="none"
              viewBox="0 0 24 24"
              className="flex-shrink-0 text-gray-300"
            >
              <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
}
