import Link from 'next/link';

const tests = [
  { label: 'Malaria RDT', href: '/scan' },
  { label: 'COVID-19 RDT', href: '/scan' },
  { label: 'Pregnancy Test', href: '/scan' },
  { label: 'HIV RDT', href: '/scan' },
];

const resources = [
  { label: 'How it works', href: '#how-it-works' },
  { label: 'About Stria', href: '#about' },
  { label: 'WHO RDT Guidelines', href: '#' },
  { label: 'GHS Protocol Library', href: '#' },
];

export default function Footer() {
  return (
    <footer style={{ backgroundColor: '#0a1e46' }}>
      {/* Main columns */}
      <div className="max-w-6xl mx-auto px-4 md:px-8 pt-16 pb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">

          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-1">
            <p className="font-bold text-2xl tracking-widest text-white mb-3">STRIA</p>
            <p className="text-sm leading-relaxed" style={{ color: 'rgba(255,255,255,0.55)' }}>
              AI-powered RDT reading for community health workers. Faster, more accurate
              results — on any smartphone.
            </p>
            {/* Social icons */}
            <div className="flex gap-4 mt-6">
              {/* Twitter / X */}
              <a href="#" aria-label="Twitter" style={{ color: 'rgba(255,255,255,0.45)' }}
                className="hover:text-white transition-colors">
                <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              {/* LinkedIn */}
              <a href="#" aria-label="LinkedIn" style={{ color: 'rgba(255,255,255,0.45)' }}
                className="hover:text-white transition-colors">
                <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
              {/* GitHub */}
              <a href="#" aria-label="GitHub" style={{ color: 'rgba(255,255,255,0.45)' }}
                className="hover:text-white transition-colors">
                <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Tests */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-5"
              style={{ color: 'rgba(255,255,255,0.4)' }}>
              Tests
            </p>
            <ul className="space-y-3">
              {tests.map((item) => (
                <li key={item.label}>
                  <Link href={item.href}
                    className="text-sm transition-colors hover:text-white"
                    style={{ color: 'rgba(255,255,255,0.65)' }}>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-5"
              style={{ color: 'rgba(255,255,255,0.4)' }}>
              Resources
            </p>
            <ul className="space-y-3">
              {resources.map((item) => (
                <li key={item.label}>
                  <a href={item.href}
                    className="text-sm transition-colors hover:text-white"
                    style={{ color: 'rgba(255,255,255,0.65)' }}>
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Project info */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-5"
              style={{ color: 'rgba(255,255,255,0.4)' }}>
              Project
            </p>
            <ul className="space-y-3 text-sm" style={{ color: 'rgba(255,255,255,0.65)' }}>
              <li>KNUST, Kumasi</li>
              <li>Ashanti Region, Ghana</li>
              <li className="pt-1">
                <a href="mailto:jgmanana@st.knust.edu.gh"
                  className="hover:text-white transition-colors break-all">
                  jgmanana@st.knust.edu.gh
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="max-w-6xl mx-auto px-4 md:px-8">
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }} />
      </div>

      {/* Bottom bar */}
      <div className="max-w-6xl mx-auto px-4 md:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs"
        style={{ color: 'rgba(255,255,255,0.35)' }}>
        <span>© 2026 Stria · KNUST · All rights reserved</span>
        <span
          className="border rounded px-2 py-0.5 font-medium"
          style={{ borderColor: 'rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.5)' }}>
          Not a medical device
        </span>
      </div>
    </footer>
  );
}
