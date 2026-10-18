import { useState } from 'react';
import Header from './components/Header';
import UploadPanel from './components/UploadPanel';
import LoadingState from './components/LoadingState';
import ErrorMessage from './components/ErrorMessage';
import EmptyState from './components/EmptyState';
import AnalysisDashboard from './components/AnalysisDashboard';
import { useAnalysis } from './hooks/useAnalysis';
import { deleteSession } from './services/api';
import './App.css';

export default function App() {
  const [file, setFile] = useState(null);
  const [sessionError, setSessionError] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const { status, result, error, run, cancel, reset } = useAnalysis();

  async function removeSession(sessionId) {
    try {
      await deleteSession(sessionId);
      setSessionError('');
      setSessionToDelete(null);
      return true;
    } catch (deleteError) {
      setSessionToDelete(sessionId);
      setSessionError(
        deleteError instanceof Error ? deleteError.message : 'Could not delete the document session.',
      );
      return false;
    }
  }

  function handleFileChange(nextFile) {
    setSessionError('');
    setFile(nextFile);
    if (result?.sessionId) {
      void removeSession(result.sessionId);
    }
    reset();
  }

  function handleAnalyze() {
    if (file) run(file);
  }

  async function handleClearDocument() {
    setSessionError('');
    if (result?.sessionId && !(await removeSession(result.sessionId))) return;
    reset();
    setFile(null);
  }

  async function retrySessionDeletion() {
    if (sessionToDelete) await removeSession(sessionToDelete);
  }

  return (
    <div className="app" id="top">
      <a className="skip-link" href="#main">Skip to content</a>
      <Header />

      <main id="main" className="container main">
        <section className="intro">
          <h1 className="intro__title">Review your document</h1>
          <p className="intro__text">Upload a PDF or text agreement to see a summary, key clauses, and cited passages.</p>
        </section>

        <UploadPanel
          file={file}
          onFileChange={handleFileChange}
          onAnalyze={handleAnalyze}
          status={status}
        />

        <div id="analysis" className="analysis-region">
          {status === 'idle' && <EmptyState />}
          {status === 'loading' && <LoadingState fileName={file?.name} onCancel={cancel} />}
          {status === 'error' && (
            <ErrorMessage error={error} onRetry={handleAnalyze} />
          )}
          {status === 'success' && result && (
            <>
              <AnalysisDashboard result={result} />
              <div className="clear-document">
                <button type="button" className="btn btn--ghost" onClick={() => void handleClearDocument()}>
                  Delete document and start over
                </button>
              </div>
            </>
          )}
        </div>
        {sessionError && (
          <div className="session-error" role="alert">
            <p>{sessionError}</p>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => void retrySessionDeletion()}>
              Retry deletion
            </button>
          </div>
        )}
      </main>

      <footer className="site-footer">
        <div className="container">
          <p className="muted small">
            Preliminary document understanding only, not legal advice. Verify findings against the original document.
          </p>
        </div>
      </footer>
    </div>
  );
}
