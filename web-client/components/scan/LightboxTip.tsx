'use client';

import Image from 'next/image';

interface Props {
  onDismiss: () => void;
}

export default function LightboxTip({ onDismiss }: Props) {
  const dismiss = () => {
    localStorage.setItem('stria_lightbox_dismissed', 'true');
    onDismiss();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-end">
      <div className="w-full bg-white rounded-t-2xl p-6 shadow-2xl">
        <h2 className="text-lg font-bold text-gray-900 mb-3">Better results</h2>
        <div className="relative w-full h-48 rounded-xl mb-4 overflow-hidden bg-gray-100">
          <Image
            src="/lightbox-guide.jpg"
            alt="Imaging stand setup"
            fill
            className="object-cover"
          />
        </div>
        <p className="text-sm text-gray-500 mb-5">
          Place the cassette flat in a small white box with LED lighting. This eliminates shadows
          and reflections that cause misreadings.
        </p>
        <button
          onClick={dismiss}
          className="w-full bg-blue-700 text-white py-3 rounded-full font-semibold hover:bg-blue-800 transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
