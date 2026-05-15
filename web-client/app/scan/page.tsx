'use client';

import { useState, useCallback } from 'react';
import TestTypeSelector from '@/components/scan/TestTypeSelector';
import CameraCapture from '@/components/scan/CameraCapture';
import ProcessingScreen from '@/components/scan/ProcessingScreen';
import ResultCard from '@/components/scan/ResultCard';
import AssistantDrawer from '@/components/scan/AssistantDrawer';
import { readCassette } from '@/lib/api';
import type { CassetteType, ReadResponse } from '@/lib/types';

type Step = 'select' | 'capture' | 'processing' | 'result';

export default function ScanPage() {
  const [step, setStep] = useState<Step>('select');
  const [cassetteType, setCassetteType] = useState<CassetteType>('malaria');
  const [capturedDataUrl, setCapturedDataUrl] = useState<string | null>(null);
  const [result, setResult] = useState<ReadResponse | null>(null);
  const [captureError, setCaptureError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleTypeSelect = useCallback((type: CassetteType) => {
    setCassetteType(type);
    setCaptureError(null);
    setStep('capture');
  }, []);

  const handleCapture = useCallback(
    async (blob: Blob, dataUrl: string) => {
      setCapturedDataUrl(dataUrl);
      setCaptureError(null);
      setStep('processing');
      try {
        const file = new File([blob], 'cassette.jpg', { type: 'image/jpeg' });
        const res = await readCassette(file, cassetteType);
        setResult(res);
        setStep('result');
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Upload failed. Please try again.';
        setCaptureError(msg);
        setStep('capture');
      }
    },
    [cassetteType],
  );

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {step === 'select' && <TestTypeSelector onSelect={handleTypeSelect} />}

      {step === 'capture' && (
        <CameraCapture
          cassetteType={cassetteType}
          onCapture={handleCapture}
          onBack={() => setStep('select')}
          errorMessage={captureError}
        />
      )}

      {step === 'processing' && capturedDataUrl && (
        <ProcessingScreen backgroundUrl={capturedDataUrl} />
      )}

      {step === 'result' && result && (
        <>
          <ResultCard
            result={result}
            onAskQuestion={() => setDrawerOpen(true)}
            onScanAnother={() => {
              setResult(null);
              setStep('capture');
            }}
            onBack={() => setStep('capture')}
          />
          {drawerOpen && (
            <AssistantDrawer result={result} onClose={() => setDrawerOpen(false)} />
          )}
        </>
      )}
    </div>
  );
}
