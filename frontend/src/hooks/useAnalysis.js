import { useCallback, useEffect, useRef, useState } from 'react';
import { analyzeDocument } from '../services/api';

// Owns the request lifecycle (idle -> loading -> success | error) so components
// only render state and call actions.
export function useAnalysis() {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const controllerRef = useRef(null);

  const run = useCallback(async (file) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setStatus('loading');
    setError(null);
    setResult(null);

    try {
      const analysis = await analyzeDocument(file, { signal: controller.signal });
      if (controllerRef.current !== controller) return;
      setResult({ ...analysis, fileName: file.name });
      setStatus('success');
    } catch (err) {
      if (controllerRef.current !== controller) return;
      if (err?.kind === 'cancelled') {
        setStatus('idle');
        return;
      }
      setError(err);
      setStatus('error');
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setStatus('idle');
    setResult(null);
    setError(null);
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { status, result, error, run, cancel, reset };
}
