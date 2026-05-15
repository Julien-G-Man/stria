import Link from 'next/link';
import Image from 'next/image';

export default function Hero() {
  return (
    <section className="relative h-screen min-h-[600px] flex items-center overflow-hidden">
      {/* Background image */}
      <Image
        src="/phone-hold.jpg"
        alt=""
        fill
        priority
        className="object-cover object-center"
      />

      {/* Cinematic gradient — dark left edge fading right, deeper at bottom */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(105deg, rgba(4,8,18,0.88) 0%, rgba(4,8,18,0.65) 45%, rgba(4,8,18,0.18) 100%), ' +
            'linear-gradient(to top, rgba(4,8,18,0.6) 0%, transparent 55%)',
        }}
      />

      {/* Content */}
      <div className="relative z-10 px-6 md:px-16 max-w-3xl w-full">
        <p className="text-white/50 text-xs font-semibold tracking-[0.2em] uppercase mb-5">
          AI · RDT · Community Health
        </p>
        <h1 className="text-4xl sm:text-5xl md:text-[4.5rem] font-bold text-white leading-[1.05] tracking-tight">
          Seeing what the{' '}
          <span style={{ color: '#5b9bd5' }}>human eye misses.</span>
        </h1>
        <p className="mt-5 text-base md:text-lg text-white/80 max-w-md leading-relaxed">
          AI-powered RDT reading for community health workers in Ghana.
          Malaria, COVID, pregnancy, and HIV — results in under 4 seconds.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/scan"
            className="bg-white text-gray-900 px-8 py-4 rounded-full text-sm font-bold hover:bg-gray-100 transition-colors"
          >
            Start Scan →
          </Link>
          <a
            href="#how-it-works"
            className="text-white/90 px-8 py-4 rounded-full text-sm font-semibold transition-colors hover:bg-white/10"
            style={{ border: '1px solid rgba(255,255,255,0.3)' }}
          >
            How it works
          </a>
        </div>
      </div>

      {/* Scroll chevron */}
      <div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce"
        style={{ color: 'rgba(255,255,255,0.35)' }}
      >
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </section>
  );
}
