import { config } from '../config';

const ALLOWED = {
  pdf: ['application/pdf', 'application/x-pdf'],
  txt: ['text/plain'],
};

export const ACCEPT_ATTRIBUTE = '.pdf,.txt,application/pdf,text/plain';

function extensionOf(name) {
  const match = /\.([^.]+)$/.exec(name || '');
  return match ? match[1].toLowerCase() : '';
}

// Returns null when the file is acceptable, otherwise a user-facing message.
export function validateFile(file) {
  if (!file) return 'No file selected.';

  const ext = extensionOf(file.name);
  if (!ALLOWED[ext]) {
    return `"${file.name}" is not supported. Please choose a PDF or TXT file.`;
  }
  // Some browsers report an empty MIME type; fall back to the extension check then.
  if (file.type && !ALLOWED[ext].includes(file.type)) {
    return `"${file.name}" does not look like a valid ${ext.toUpperCase()} file (reported type: ${file.type}).`;
  }
  if (file.size === 0) {
    return `"${file.name}" is empty.`;
  }
  const maxBytes = config.maxFileMb * 1024 * 1024;
  if (file.size > maxBytes) {
    return `"${file.name}" is larger than the ${config.maxFileMb} MB limit.`;
  }
  return null;
}
