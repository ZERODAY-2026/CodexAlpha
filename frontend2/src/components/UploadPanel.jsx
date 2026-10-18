import { useId, useRef, useState } from 'react';
import { CircleCheck, FileSearch, FileText, RefreshCw, Upload, X } from 'lucide-react';
import { config } from '../config';
import { ACCEPT_ATTRIBUTE, validateFile } from '../utils/fileValidation';
import { formatBytes } from '../utils/format';

export default function UploadPanel({ file, onFileChange, onAnalyze, status }) {
  const inputRef = useRef(null);
  const inputId = useId();
  const hintId = useId();
  const [validationError, setValidationError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const isLoading = status === 'loading';

  function handleFiles(fileList) {
    const candidate = fileList?.[0];
    if (!candidate) return;
    const problem = validateFile(candidate);
    setValidationError(problem);
    if (!problem) onFileChange(candidate);
  }

  function openPicker() {
    inputRef.current?.click();
  }

  function handleInputChange(event) {
    handleFiles(event.target.files);
    // Reset so selecting the same file again still fires a change event.
    event.target.value = '';
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    if (!isLoading) handleFiles(event.dataTransfer.files);
  }

  function handleRemove() {
    setValidationError(null);
    onFileChange(null);
  }

  return (
    <section id="upload" className="card upload-panel" aria-labelledby="upload-heading">
      <div className="card__header">
        <div>
          <h2 id="upload-heading" className="card__title">Upload a document</h2>
          <p className="muted">PDF or TXT, up to {config.maxFileMb} MB.</p>
        </div>
      </div>

      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={ACCEPT_ATTRIBUTE}
        className="visually-hidden"
        onChange={handleInputChange}
        disabled={isLoading}
        aria-describedby={hintId}
        tabIndex={-1}
      />

      {!file ? (
        <div
          className={`dropzone ${isDragging ? 'is-dragging' : ''} ${validationError ? 'has-error' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <Upload size={28} aria-hidden="true" className="dropzone__icon" />
          <p className="dropzone__title">Drag and drop your document here</p>
          <p id={hintId} className="muted small">Accepted formats: .pdf, .txt</p>
          <button type="button" className="btn btn--secondary" onClick={openPicker} disabled={isLoading}>
            Choose file
          </button>
        </div>
      ) : (
        <div className="file-row">
          <span className="file-row__icon" aria-hidden="true">
            <FileText size={22} />
          </span>
          <div className="file-row__meta">
            <p className="file-row__name" title={file.name}>{file.name}</p>
            <p className="muted small">
              {formatBytes(file.size)}
              {status === 'success' && (
                <span className="file-row__done">
                  <CircleCheck size={14} aria-hidden="true" /> Analysed
                </span>
              )}
            </p>
          </div>
          <div className="file-row__actions">
            <button type="button" className="btn btn--ghost btn--sm" onClick={openPicker} disabled={isLoading}>
              <RefreshCw size={15} aria-hidden="true" /> Replace
            </button>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={handleRemove}
              disabled={isLoading}
              aria-label={`Remove ${file.name}`}
            >
              <X size={15} aria-hidden="true" /> Remove
            </button>
          </div>
        </div>
      )}

      {validationError && (
        <p className="field-error" role="alert">
          {validationError}
        </p>
      )}

      <div className="upload-panel__footer upload-panel__footer--simple">
        <button
          type="button"
          className="btn btn--primary btn--lg"
          onClick={onAnalyze}
          disabled={!file || isLoading}
        >
          <FileSearch size={18} aria-hidden="true" />
          {isLoading ? 'Analysing…' : 'Analyze Document'}
        </button>
      </div>
    </section>
  );
}
