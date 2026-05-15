import Link from 'next/link';

const types = [
  {
    emoji: '🦟',
    name: 'Malaria',
    scientific: 'Plasmodium falciparum',
    description:
      'Detects HRP2 and pLDH antigens. Covers P. falciparum and mixed infections. Most critical RDT use case in Ghana.',
    accent: '#dc2626',
    accentBg: '#fef2f2',
    tag: 'Most common',
  },
  {
    emoji: '🦠',
    name: 'COVID-19',
    scientific: 'SARS-CoV-2',
    description:
      'Nucleocapsid antigen detection. Rapid triage in community settings without PCR infrastructure.',
    accent: '#2563eb',
    accentBg: '#eff6ff',
    tag: null,
  },
  {
    emoji: '🤰',
    name: 'Pregnancy',
    scientific: 'hCG hormone',
    description:
      'Human chorionic gonadotropin strip test. Supports antenatal registration and early care referrals.',
    accent: '#db2777',
    accentBg: '#fdf2f8',
    tag: null,
  },
  {
    emoji: '🩸',
    name: 'HIV',
    scientific: 'HIV-1 / HIV-2',
    description:
      'Antibody detection for HIV-1 and HIV-2. Enables same-day status disclosure and linkage to ART.',
    accent: '#d97706',
    accentBg: '#fffbeb',
    tag: null,
  },
];

export default function TestTypeGrid() {
  return (
    <section className="bg-white py-20 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
          <div>
            <p className="text-blue-700 font-semibold text-sm uppercase tracking-widest mb-2">
              Supported tests
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 leading-tight">
              Four diseases.<br className="hidden sm:block" /> One interface.
            </h2>
          </div>
          <Link
            href="/scan"
            className="self-start sm:self-auto shrink-0 bg-blue-700 text-white px-6 py-3 rounded-full text-sm font-semibold hover:bg-blue-800 transition-colors"
          >
            Start scanning →
          </Link>
        </div>

        {/* Cards grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {types.map((t) => (
            <div
              key={t.name}
              className="rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden"
              style={{ backgroundColor: t.accentBg }}
            >
              {/* Tag */}
              {t.tag && (
                <span
                  className="absolute top-4 right-4 text-xs font-semibold px-2 py-0.5 rounded-full text-white"
                  style={{ backgroundColor: t.accent }}
                >
                  {t.tag}
                </span>
              )}

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                style={{ backgroundColor: `${t.accent}22` }}
              >
                {t.emoji}
              </div>

              {/* Text */}
              <div>
                <p className="font-bold text-gray-900 text-lg leading-tight">{t.name}</p>
                <p className="text-xs font-medium mt-0.5" style={{ color: t.accent }}>
                  {t.scientific}
                </p>
              </div>

              <p className="text-sm text-gray-500 leading-relaxed flex-1">
                {t.description}
              </p>

              {/* Accent line at bottom */}
              <div
                className="h-0.5 w-10 rounded-full mt-1"
                style={{ backgroundColor: t.accent }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
