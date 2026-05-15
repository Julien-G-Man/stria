const stats = [
  { value: '600K+', label: 'malaria deaths per year' },
  { value: 'up to 30%', label: 'RDT misread rate (WHO)' },
  { value: '200M+', label: 'tests/yr in SSA' },
];

export default function StatsBar() {
  return (
    <section className="bg-gray-100 py-10 px-4 md:px-6">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-3 gap-4 text-center">
          {stats.map((s) => (
            <div key={s.value}>
              <p className="text-4xl font-bold text-blue-700">{s.value}</p>
              <p className="text-sm text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
