# Local model

- Runtime: Ollama's local HTTP API on `http://127.0.0.1:11434`.
- Default model tag: `gemma4:e2b` (environment override: `OLLAMA_MODEL`).
- Observed local build: `nvfp4`, 7,477,041,465 bytes on disk; `ollama show` reports Gemma 4 architecture and 5.2B parameters.
- Observed license reported by local `ollama show`: Apache License 2.0. Review and accept the model license when obtaining model weights; this repository does not bundle them.
- The checked-in values above describe only the local model installation used for [the benchmark](./BENCHMARKS.md). Inspect `ollama show gemma4:e2b` and `ollama list` on another machine rather than assuming its quantization or disk size.
- Runtime configuration: temperature `0.1`; output is requested as JSON for structured tasks.
- Data flow: prompts, questions and document text go only to loopback Ollama. No model downloader is invoked by the app.
