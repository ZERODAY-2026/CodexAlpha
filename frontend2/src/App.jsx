import { useState } from 'react';
import Header from './components/Header';
import UploadPanel from './components/UploadPanel';
import LoadingState from './components/LoadingState';
import ErrorMessage from './components/ErrorMessage';
import EmptyState from './components/EmptyState';
import AnalysisDashboard from './components/AnalysisDashboard';
import AboutSection from './components/AboutSection';
import { useAnalysis } from './hooks/useAnalysis';
import { config } from './config';
import './App.css';

export default function App() {
  const [file, setFile] = useState(null);
  const [useMock, setUseMock] = useState(config.useMockByDefault);
  const { status, result, error, run, cancel, reset } = useAnalysis();

  function handleFileChange(nextFile) {
    setFile(nextFile);
    // A new or removed file invalidates the previous analysis.
    reset();
  }

  function handleModeChange(nextUseMock) {
    setUseMock(nextUseMock);
    reset();
  }

  function handleAnalyze() {
    if (file) run(file, { useMock });
  }

  function handleSwitchToDemo() {
    setUseMock(true);
    if (file) run(file, { useMock: true });
  }

  // Privacy status is only taken from a real backend response.
  const processing = result?.source === 'api' ? result.processing : null;

  return (
    <div className="app" id="top">
      <a className="skip-link" href="#main">Skip to content</a>
      <Header useMock={useMock} processing={processing} />

      <main id="main" className="container main">
        <section className="intro">
          <h1 className="intro__title">Understand a legal document before you sign it.</h1>
          <p className="intro__text">
            Upload a rental agreement or similar document to get a plain-language summary, the clauses that matter, and
            the exact passages behind every finding. Results are a preliminary reading, not legal advice.
          </p>
        </section>

        <UploadPanel
          file={file}
          onFileChange={handleFileChange}
          onAnalyze={handleAnalyze}
          status={status}
          useMock={useMock}
          onModeChange={handleModeChange}
        />

        <div id="analysis" className="analysis-region">
          {status === 'idle' && <EmptyState />}
          {status === 'loading' && <LoadingState fileName={file?.name} useMock={useMock} onCancel={cancel} />}
          {status === 'error' && (
            <ErrorMessage error={error} onRetry={handleAnalyze} onSwitchToDemo={useMock ? null : handleSwitchToDemo} />
          )}
          {status === 'success' && result && <AnalysisDashboard result={result} />}
        </div>

        <AboutSection />
      </main>

      <footer className="site-footer">
        <div className="container">
          <p className="muted small">
            Private Legal Triage provides preliminary document understanding, not definitive legal advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
