'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-4 md:px-8 transition-all duration-300"
      style={{
        backgroundColor: scrolled ? 'rgba(255,255,255,0.97)' : 'transparent',
        borderBottom: scrolled ? '1px solid #f3f4f6' : 'none',
        boxShadow: scrolled ? '0 1px 12px rgba(0,0,0,0.06)' : 'none',
        backdropFilter: scrolled ? 'blur(8px)' : 'none',
      }}
    >
      {/* Logo */}
      <Link
        href="/"
        className="font-bold text-xl tracking-widest transition-colors duration-300"
        style={{ color: scrolled ? '#1A56A0' : '#ffffff' }}
      >
        STRIA
      </Link>

      {/* CTA button */}
      <Link
        href="/scan"
        className="px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300"
        style={
          scrolled
            ? { backgroundColor: '#1A56A0', color: '#ffffff' }
            : {
                backgroundColor: 'rgba(255,255,255,0.18)',
                color: '#ffffff',
                border: '1px solid rgba(255,255,255,0.4)',
              }
        }
      >
        Start Scan
      </Link>
    </nav>
  );
}
