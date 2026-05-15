import Image from 'next/image';

interface Step {
  number: string;
  title: string;
  body: string;
  image: string;
  imageAlt: string;
  reverse: boolean;
}

const steps: Step[] = [
  {
    number: '01',
    title: 'Place the cassette',
    body: 'Set the RDT cassette on a flat surface with good lighting. For best results, use the simple lightbox stand — it eliminates shadows and reflection that confuse the AI.',
    image: '/phone-capture.jpg',
    imageAlt: 'Community health worker holding an RDT cassette',
    reverse: false,
  },
  {
    number: '02',
    title: 'Capture a photo',
    body: 'Open the app and point your phone camera at the cassette. Stria auto-detects the cassette shape and captures automatically when it is steady in frame — or tap the button to capture manually.',
    image: '/phone-model-03.webp',
    imageAlt: 'Phone showing Stria app scanning interface',
    reverse: true,
  },
  {
    number: '03',
    title: 'Read results in 4 seconds',
    body: 'The AI interprets control and test lines, classifies the outcome, and shows the clinical protocol for that result. Positive, negative, or invalid — you always know what to do next.',
    image: '/read-phone-results.jpg',
    imageAlt: 'RDT result displayed on screen',
    reverse: false,
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-white py-20 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-14 max-w-xl">
          <p className="text-blue-700 font-semibold text-sm uppercase tracking-widest mb-2">
            How it works
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 leading-tight">
            Three steps. Under a minute.
          </h2>
        </div>

        <div className="flex flex-col gap-20">
          {steps.map((step) => (
            <div
              key={step.number}
              className={`flex flex-col ${step.reverse ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-8 md:gap-16`}
            >
              {/* Image */}
              <div className="w-full md:w-1/2 flex-shrink-0">
                <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden shadow-sm">
                  <Image
                    src={step.image}
                    alt={step.imageAlt}
                    fill
                    className="object-cover"
                  />
                </div>
              </div>

              {/* Text */}
              <div className="w-full md:w-1/2">
                <p className="text-blue-700 font-bold text-sm tracking-widest mb-3">
                  {step.number}
                </p>
                <h3 className="text-2xl md:text-3xl font-bold text-gray-900 leading-snug mb-4">
                  {step.title}
                </h3>
                <p className="text-gray-500 text-base md:text-lg leading-relaxed">
                  {step.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
