# Five-minute demo script

1. **Local start (30 seconds):** Show Ollama listening at `127.0.0.1:11434`, start FastAPI with `--host 127.0.0.1 --no-access-log`, and open `http://127.0.0.1:8000/`. Point out the persistent preliminary-understanding disclaimer.
2. **Normal analysis (60 seconds):** Upload `sample_docs/rental_agreement_sample.txt`. Show progress, cited overview, key clauses, and source pages.
3. **Cited answer (45 seconds):** Ask “When is rent due?” Open its verified source citation and show the highlighted verbatim passage with clause and page.
4. **Silent question (45 seconds):** Ask “What color is the building?” Show the document-silent response instead of a guessed answer.
5. **Refusal (45 seconds):** Ask “Is the termination clause enforceable?” Show the refusal, cited document passages, and local professional escalation.
6. **Injection handling (45 seconds):** Delete the current session and upload `sample_docs/prompt_injection_sample.txt`. Show the suspicious-text warning; emphasize the text is shown as data and not followed.
7. **Offline run (30 seconds):** If Docker and the model volume are prepared, run `bash scripts/privacy_test.sh`. It executes the API and Ollama together with Docker `--network none`. Otherwise, show the script and network policy, and state that offline verification remains to be run.

Do not upload a real person's agreement during a public recording. Use only the fictional samples.
