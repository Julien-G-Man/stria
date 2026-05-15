'use client';

import { useState } from 'react';
import type { LineReading } from '@/lib/types';

interface Props {
  lines: LineReading;
}

function lineIcon(present: boolean, intensity?: 'strong' | 'faint' | 'absent') {
  if (!present) return { icon: '✕', cls: 'text-gray-400' };
  if (intensity === 'faint') return { icon: '⚠', cls: 'text-amber-500' };
  return { icon: '✓', cls: 'text-green-600' };
}

export default function LinesSummary({ lines }: Props) {
  const [showRaw, setShowRaw] = useState(false);
  const c = lineIcon(lines.control_line_present);
  const t = lineIcon(lines.test_line_present, lines.test_line_intensity);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">C line (Control)</span>
        <span className={`font-semibold ${c.cls}`}>
          {c.icon} {lines.control_line_present ? 'Present' : 'Absent'}
        </span>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">T line (Test)</span>
        <span className={`font-semibold ${t.cls}`}>
          {t.icon}{' '}
          {lines.test_line_intensity === 'absent'
            ? 'Absent'
            : lines.test_line_intensity.charAt(0).toUpperCase() +
              lines.test_line_intensity.slice(1)}
        </span>
      </div>
      <button
        onClick={() => setShowRaw((v) => !v)}
        className="text-xs text-gray-400 mt-2 underline"
      >
        {showRaw ? 'Hide' : 'Show'} raw observation
      </button>
      {showRaw && (
        <p className="text-xs text-gray-400 italic font-mono mt-1 leading-relaxed">
          &ldquo;{lines.raw_observation}&rdquo;
        </p>
      )}
    </div>
  );
}
