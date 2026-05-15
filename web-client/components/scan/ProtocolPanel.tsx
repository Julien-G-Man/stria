interface Props {
  protocol: Record<string, unknown>;
}

export default function ProtocolPanel({ protocol }: Props) {
  const steps = Array.isArray(protocol.steps) ? (protocol.steps as string[]) : [];
  const refer = Boolean(protocol.refer);

  return (
    <div className="bg-blue-50 rounded-2xl p-4 shadow-sm">
      <p className="text-sm font-semibold text-gray-900 mb-3">What to do next</p>
      <ul className="space-y-2">
        {steps.map((step, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
            <span className="text-blue-700 font-bold mt-0.5 shrink-0">·</span>
            <span>{step}</span>
          </li>
        ))}
      </ul>
      {refer && (
        <div className="mt-3 inline-flex items-center gap-1 bg-amber-100 border border-amber-200 text-amber-700 text-xs px-3 py-1 rounded-lg">
          ⚠ Referral needed
        </div>
      )}
    </div>
  );
}
