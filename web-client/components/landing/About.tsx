const stats = [
  { value: '< 4s', label: 'Time to result' },
  { value: '4', label: 'Test types supported' },
  { value: '0', label: 'Extra equipment needed' },
];

export default function About() {
  return (
    <section id="about" className="bg-white py-24 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Two-column layout on desktop */}
        <div className="flex flex-col lg:flex-row gap-16 items-start">

          {/* Left — headline block */}
          <div className="lg:w-5/12">
            <p className="text-blue-700 font-semibold text-sm uppercase tracking-widest mb-3">
              About Stria
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 leading-snug">
              Malaria kills.<br />
              Missed diagnoses<br />
              <span className="text-blue-700">don&apos;t have to.</span>
            </h2>

            {/* Stat strip */}
            <div className="mt-10 grid grid-cols-3 gap-4 border-t border-gray-100 pt-8">
              {stats.map((s) => (
                <div key={s.label}>
                  <p className="text-3xl font-bold text-blue-700">{s.value}</p>
                  <p className="text-xs text-gray-500 mt-1 leading-tight">{s.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right — body copy */}
          <div className="lg:w-7/12 space-y-5 text-gray-600 text-base md:text-lg leading-relaxed">
            <p>
              Stria is an AI-powered rapid diagnostic test reader built for community health
              workers in Ghana and sub-Saharan Africa. Using nothing more than a smartphone
              camera, it interprets the control and test lines of an RDT cassette in under
              four seconds — eliminating the human misreadings that delay treatment and
              cost lives.
            </p>
            <p>
              RDT misread rates can reach 30% in field conditions. Faint lines are dismissed.
              Invalid tests are reported as negative. Stria removes that uncertainty: a
              single photo triggers a computer-vision pipeline that classifies the result,
              quantifies its confidence, and immediately surfaces the clinical protocol a
              health worker should follow.
            </p>
            <p>
              Designed to work in low-connectivity environments, Stria requires no
              specialised equipment and no laboratory training. It supports malaria,
              COVID-19, pregnancy, and HIV cassettes — with more test types in development.
            </p>

            {/* Trust tags */}
            <div className="flex flex-wrap gap-2 pt-2">
              {[
                'Built at KNUST, Ghana',
                'WHO RDT Guidelines',
                'GHS Protocol Library',
                'Works offline',
                'No lab training required',
              ].map((tag) => (
                <span
                  key={tag}
                  className="bg-blue-50 text-blue-700 text-xs font-medium px-3 py-1 rounded-full border border-blue-100"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
