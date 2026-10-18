# Local model benchmark

- Date: 2026-10-18 12:13:27 +0530
- Hardware: arm64, arm
- OS: macOS-26.5.2-arm64-arm-64bit
- Physical RAM: 16.0 GiB
- Model: `gemma4:e2b`
- Quantization: `nvfp4`
- Model size on disk: 7477041465 bytes

| Task | Latency (s) | Eval tokens | Tokens/s |
|---|---:|---:|---:|
| summary | 3.21 | 256 | 80.88 |
| clause explanation | 3.35 | 256 | 77.32 |
| question answering | 2.41 | 190 | 80.26 |

- Ollama reported loaded model memory: 7.7 GB
- Ollama reported processor placement: 100% GPU
- Ollama process RSS after tasks (does not include all GPU/unified-memory allocations): 169.1 MiB

Benchmarks use synthetic prompts only. `ollama ps` reports loaded model memory/placement; process RSS does not include all GPU or unified-memory allocations. Latency and memory vary by device, model build, quantization, and concurrent load.
