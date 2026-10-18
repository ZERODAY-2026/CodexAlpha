# Limitations

- This is preliminary document understanding, not legal advice. It must not be used to decide whether a clause or agreement is legal, valid, or enforceable, to predict a case outcome, or to decide whether to sign.
- The intended scope is rental and employment agreements supplied as text-based PDFs or plain-text files. Other content and scanned/image-only PDFs are not reliably supported. OCR is not included.
- Model-generated summaries, explanations, interpretations and concern flags may be incomplete or mistaken. Citation checking confirms only that a quoted passage exists in the referenced clause; it does not prove that an explanation follows from the quote.
- BM25 is lexical retrieval and may miss relevant clauses phrased differently from the question.
- Risk checks are simple heuristics and can produce false positives or miss issues. Absence flags describe only phrases that the app did not find; they do not establish that a document lacks a legal requirement.
- Local model quality and latency depend on installed model files and device hardware. Responses can be slow, malformed, or unavailable if Ollama is stopped.
- The prototype does not identify jurisdiction or state applicable law. Local law may affect topics such as notice periods, deposits, non-competes, penalties, stamp duty and registration.
- Sessions exist only in backend memory, expire after the configured TTL, and are lost on server restart. This is not durable or encrypted document storage.
