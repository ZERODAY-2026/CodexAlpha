#!/usr/bin/env python3
"""Benchmark local Ollama latency and report model/device metadata."""
from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL  # noqa: E402
from src.llm import _assert_loopback  # noqa: E402

TASKS = [
    ("summary", "Summarize in one sentence: A fictional agreement describes a monthly rent payment and a 30-day notice period."),
    ("clause explanation", "Explain in plain language: The tenant shall pay rent on the first day of each month."),
    ("question answering", "Return JSON: What is the rent deadline? Passage: Rent is due on the fifth day of each month."),
]


def model_size_bytes(model: str) -> int | None:
    model_name, _, tag = model.rpartition(":")
    if not tag:
        model_name, tag = model, "latest"
    manifest = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library" / model_name / tag
    if not manifest.is_file():
        return None
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    digests = {
        layer.get("digest")
        for layer in [manifest_data.get("config", {}), *manifest_data.get("layers", [])]
        if isinstance(layer, dict) and isinstance(layer.get("digest"), str)
    }
    total = 0
    for digest in digests:
        blob = Path.home() / ".ollama" / "models" / "blobs" / digest.replace(":", "-", 1)
        if blob.is_file():
            total += blob.stat().st_size
    return total or None


def ollama_rss_mb() -> float | None:
    try:
        output = subprocess.check_output(["ps", "-axo", "rss=,comm="], text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    rss_kb = 0
    for line in output.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2 and re.search(r"ollama", fields[1], re.IGNORECASE):
            try:
                rss_kb += int(fields[0])
            except ValueError:
                continue
    return round(rss_kb / 1024, 1) if rss_kb else None


def machine_ram_gb() -> float | None:
    try:
        raw = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        return round(int(raw) / (1024 ** 3), 1)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def loaded_model_info(model: str) -> tuple[str, str] | None:
    try:
        output = subprocess.check_output(["ollama", "ps"], text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    for line in output.splitlines()[1:]:
        fields = line.split()
        if fields and fields[0] == model and len(fields) >= 4:
            return " ".join(fields[2:4]), " ".join(fields[4:6])
    return None


def main() -> int:
    _assert_loopback(OLLAMA_BASE_URL)
    try:
        model_info = requests.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/show",
            json={"model": OLLAMA_MODEL},
            timeout=15,
        )
        model_info.raise_for_status()
        model_details = model_info.json().get("details", {})
    except requests.RequestException as exc:
        print(f"Local Ollama is unavailable: {exc}", file=sys.stderr)
        return 1

    report = [
        "# Local model benchmark",
        "",
        f"- Date: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"- Hardware: {platform.machine()}, {platform.processor() or 'processor unavailable'}",
        f"- OS: {platform.platform()}",
        f"- Physical RAM: {machine_ram_gb() or 'unavailable'} GiB",
        f"- Model: `{OLLAMA_MODEL}`",
        f"- Quantization: `{model_details.get('quantization_level', 'not reported by Ollama')}`",
        f"- Model size on disk: {model_size_bytes(OLLAMA_MODEL) or 'unavailable'} bytes",
        "",
        "| Task | Latency (s) | Eval tokens | Tokens/s |",
        "|---|---:|---:|---:|",
    ]
    for name, prompt in TASKS:
        started = time.perf_counter()
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 256},
                },
                timeout=600,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Local benchmark failed on task {name}: {exc}", file=sys.stderr)
            return 1
        elapsed = time.perf_counter() - started
        stats = response.json()
        tokens = int(stats.get("eval_count", 0))
        eval_duration = float(stats.get("eval_duration", 0))
        token_rate = tokens / (eval_duration / 1_000_000_000) if eval_duration else 0.0
        report.append(f"| {name} | {elapsed:.2f} | {tokens} | {token_rate:.2f} |")

    running_info = loaded_model_info(OLLAMA_MODEL)
    report.extend([
        "",
        f"- Ollama reported loaded model memory: {running_info[0] if running_info else 'unavailable'}",
        f"- Ollama reported processor placement: {running_info[1] if running_info else 'unavailable'}",
        f"- Ollama process RSS after tasks (does not include all GPU/unified-memory allocations): {ollama_rss_mb() or 'unavailable'} MiB",
        "",
        "Benchmarks use synthetic prompts only. `ollama ps` reports loaded model memory/placement; process RSS does not include all GPU or unified-memory allocations. Latency and memory vary by device, model build, quantization, and concurrent load.",
        "",
    ])
    output = "\n".join(report)
    destination = ROOT / "docs" / "BENCHMARKS.md"
    destination.write_text(output, encoding="utf-8")
    print(output)
    print(f"Saved benchmark report to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
