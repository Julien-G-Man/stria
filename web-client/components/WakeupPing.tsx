'use client';

import { useEffect } from 'react';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function WakeupPing() {
  useEffect(() => {
    fetch(`${BASE}/health`).catch(() => {});
  }, []);
  return null;
}
