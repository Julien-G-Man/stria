import Link from 'next/link';

const metrics = [
  { label: 'Trace depth', value: '12x' },
  { label: 'Signal fidelity', value: '99.2%' },
  { label: 'Review cycle', value: '< 5 min' },
];

const steps = [
  'Ingest documents and surface the relevant spans.',
  'Cross-link results with retrieval, imaging, and assistant workflows.',
  'Ship a fast interface that keeps the reading path visible.',
];

export default function Home() {
  return (
    <main className="shell">
      <section className="hero">
        <div className="eyebrow">Stria Web Client</div>
        <h1>Build a sharp reading workspace for the Stria pipeline.</h1>
        <p className="lede">
          This Next.js app gives the backend a clean, fast front end for document
          review, retrieval, and guided analysis.
        </p>

        <div className="actions">
          <Link className="primary" href="/">
            Open dashboard
          </Link>
          <Link className="secondary" href="/">
            View docs
          </Link>
        </div>
      </section>

      <section className="panel metrics" aria-label="Key metrics">
        {metrics.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="panel workflow">
        <div>
          <p className="section-label">Workflow</p>
          <h2>Opinionated, minimal, and ready to connect to the Python service layer.</h2>
        </div>

        <ol>
          {steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>
    </main>
  );
}
