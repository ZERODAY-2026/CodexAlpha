"""Manually stream Open India Law legislation into a small local JSONL subset.

This setup-only script downloads the gated legislation configuration when run by
the user. It never reads or requests judgments, Qdrant snapshots, or embeddings.
"""
from __future__ import annotations

import argparse
import difflib
import itertools
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping


ROOT = Path(__file__).resolve().parent.parent
DATASET_ID = "vaquill/open-india-law"
DATASET_CONFIG = "legislation"
SNAPSHOT = "v2026.08"
DEFAULT_CONFIG = ROOT / "config" / "statute_acts.json"
DEFAULT_OUTPUT = ROOT / "data" / "statutes"
DATASET_CARD = "https://huggingface.co/datasets/vaquill/open-india-law"


def _load_dataset_stream() -> Iterable[Mapping[str, Any]]:
    """Use the user's cached Hugging Face login or HF_TOKEN without exposing it."""
    from datasets import load_dataset

    return load_dataset(
        DATASET_ID,
        DATASET_CONFIG,
        split="train",
        streaming=True,
        token=True,
    )


def _normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _state(value: Any) -> str:
    return _normalise(value).replace(" ", "-") or "central"


def _token_matches(pattern_token: str, title_tokens: list[str]) -> bool:
    for token in title_tokens:
        if token == pattern_token:
            return True
        if len(pattern_token) >= 6 and len(token) >= 6:
            if difflib.SequenceMatcher(None, pattern_token, token).ratio() >= 0.82:
                return True
    return False


def _title_matches(title: Any, pattern: str) -> bool:
    title_norm = _normalise(title)
    pattern_norm = _normalise(pattern)
    if not pattern_norm:
        return False
    if pattern_norm in title_norm:
        return True
    title_tokens = title_norm.split()
    return all(_token_matches(token, title_tokens) for token in pattern_norm.split())


def _exact_title_matches(title: Any, exact_titles: list[str]) -> bool:
    normalised = _normalise(title)
    return any(normalised == _normalise(exact) for exact in exact_titles)


def _distinct_title_count(titles: Iterable[str]) -> int:
    return len({_normalise(title) for title in titles})


def _truthy(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().casefold()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _passes_default_status(row: Mapping[str, Any], include_repealed: bool) -> bool:
    if include_repealed:
        return True
    title = str(row.get("title") or "")
    if re.search(r"rep\.,", title, re.IGNORECASE):
        return False
    in_force = _truthy(row.get("in_force"))
    if in_force is False:
        return False
    status = row.get("act_status")
    if status is not None and str(status).strip().casefold() != "in_force":
        return False
    return True


def _chunk_order(chunk_id: Any) -> tuple[int, str]:
    text = str(chunk_id or "")
    suffix = re.search(r"(?:^|_)(?:[a-z])?(\d+)$", text, re.IGNORECASE)
    return (int(suffix.group(1)) if suffix else 0, text.casefold())


def _strip_act_header(text: Any) -> str:
    value = str(text or "")
    lines = value.splitlines(keepends=True)
    if lines and lines[0].lstrip().startswith("Act:"):
        return "".join(lines[1:]).strip()
    return value.strip()


def _as_year(value: Any) -> int | None:
    try:
        return int(float(value)) if value is not None and str(value).strip() else None
    except (TypeError, ValueError, OverflowError):
        return None


def _load_config(config_path: Path) -> list[dict[str, Any]]:
    entries = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("Configuration must be a JSON list.")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every configuration entry must be an object.")
        if entry.get("scope") not in {"rental", "employment", "both"}:
            raise ValueError(f"Invalid scope for entry {entry.get('name', '<unnamed>')}.")
        if not isinstance(entry.get("title_patterns"), list) or not entry["title_patterns"]:
            raise ValueError(f"Entry {entry.get('name', '<unnamed>')} needs title_patterns.")
    return entries


def _iter_rows(loader: Callable[[], Iterable[Mapping[str, Any]]]) -> Iterator[Mapping[str, Any]]:
    return iter(loader())


def _discover_titles(
    entries: list[dict[str, Any]],
    loader: Callable[[], Iterable[Mapping[str, Any]]],
    include_repealed: bool = False,
) -> tuple[dict[int, set[str]], dict[int, dict[str, set[str]]]]:
    matches_by_pattern: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    first_rows = _iter_rows(loader)
    first = next(first_rows, None)
    if first is None:
        print("COLUMNS: [] (empty legislation stream)")
        return {}, {}
    print("COLUMNS: " + ", ".join(sorted(str(key) for key in first.keys())))
    for row in itertools.chain((first,), first_rows):
        if not _passes_default_status(row, include_repealed):
            continue
        title = str(row.get("title") or "")
        if not title:
            continue
        row_state = _state(row.get("state"))
        for entry_index, entry in enumerate(entries):
            if row_state != _state(entry.get("state")):
                continue
            for pattern in entry["title_patterns"]:
                if _title_matches(title, str(pattern)):
                    matches_by_pattern[entry_index][str(pattern)].add(title)

    selected: dict[int, set[str]] = {}
    for entry_index, entry in enumerate(entries):
        all_titles = set().union(*matches_by_pattern[entry_index].values()) if matches_by_pattern[entry_index] else set()
        for pattern in entry["title_patterns"]:
            titles = sorted(matches_by_pattern[entry_index].get(str(pattern), set()), key=str.casefold)
            if not titles:
                print(f"MISSING pattern={pattern!r} act={entry['name']!r} state={_state(entry.get('state'))}")
            else:
                for title in titles:
                    print(f"MATCH pattern={pattern!r} title={title!r} state={_state(entry.get('state'))}")
                if _distinct_title_count(titles) > 1:
                    print(f"AMBIGUOUS pattern={pattern!r} act={entry['name']!r}; matched titles:")
                    for title in titles:
                        print(f"  - {title}")
        if _distinct_title_count(all_titles) > 1:
            print(f"AMBIGUOUS act={entry['name']!r}; candidate titles:")
            for title in sorted(all_titles, key=str.casefold):
                print(f"  - {title}")
            exact_titles = entry.get("exact_titles") or []
            confirmed = {title for title in all_titles if _exact_title_matches(title, exact_titles)}
            if not confirmed:
                print(f"MISSING exact_titles confirmation for act={entry['name']!r}; no candidate included")
            selected[entry_index] = confirmed
        else:
            selected[entry_index] = all_titles
        if entry.get("exact_titles"):
            confirmed = {title for title in selected[entry_index] if _exact_title_matches(title, entry["exact_titles"])}
            if not confirmed:
                print(f"MISSING exact_titles match for act={entry['name']!r}")
            selected[entry_index] = confirmed
    return selected, matches_by_pattern


def _row_matches_selection(row: Mapping[str, Any], entries: list[dict[str, Any]], selected: dict[int, set[str]]) -> bool:
    title = str(row.get("title") or "")
    row_state = _state(row.get("state"))
    title_norm = _normalise(title)
    return any(
        title in selected.get(index, set()) and row_state == _state(entry.get("state"))
        for index, entry in enumerate(entries)
    ) and bool(title_norm)


def _collect_sections(
    entries: list[dict[str, Any]],
    selected: dict[int, set[str]],
    loader: Callable[[], Iterable[Mapping[str, Any]]],
    include_repealed: bool,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in _iter_rows(loader):
        if not _row_matches_selection(row, entries, selected):
            continue
        if not _passes_default_status(row, include_repealed):
            continue
        act_id = str(row.get("act_id") or "").strip()
        if not act_id:
            continue
        section_number = str(row.get("section_number") or "").strip()
        groups[(act_id, section_number)].append(row)

    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sections: list[dict[str, Any]] = []
    for (act_id, section_number), chunks in groups.items():
        chunks.sort(key=lambda row: _chunk_order(row.get("chunk_id")))
        first = chunks[0]
        texts = [text for row in chunks if (text := _strip_act_header(row.get("text")))]
        text = "\n\n".join(texts)
        if not text:
            continue
        section_title = next((str(row.get("section_title") or "").strip() for row in chunks if row.get("section_title")), "")
        year = next((_as_year(row.get("year")) for row in chunks if _as_year(row.get("year")) is not None), None)
        status = str(first.get("act_status") or ("in_force" if _truthy(first.get("in_force")) else "unknown"))
        source_url = next((str(row.get("source_url")).strip() for row in chunks if row.get("source_url")), "")
        mirror_url = next((str(row.get("mirror_url")).strip() for row in chunks if row.get("mirror_url")), "")
        sections.append({
            "act_id": act_id,
            "title": str(first.get("title") or ""),
            "state": _state(first.get("state")),
            "year": year,
            "section_number": section_number,
            "section_title": section_title,
            "text": text,
            "act_status": status,
            "in_force": _truthy(first.get("in_force")),
            "source_url": source_url,
            "mirror_url": mirror_url,
            "source_publisher": str(first.get("source_publisher") or ""),
            "snapshot": SNAPSHOT,
            "fetched_at": fetched_at,
        })
    sections.sort(key=lambda item: (_state(item["state"]), str(item["title"]).casefold(), item["section_number"]))
    return sections


def build_subset(
    config_path: Path = DEFAULT_CONFIG,
    output_dir: Path = DEFAULT_OUTPUT,
    include_repealed: bool = False,
    loader: Callable[[], Iterable[Mapping[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    entries = _load_config(config_path)
    dataset_loader = loader or _load_dataset_stream
    try:
        selected, _ = _discover_titles(entries, dataset_loader, include_repealed)
        if not selected:
            print("MISSING: no configured Act titles matched the legislation stream")
        sections = _collect_sections(entries, selected, dataset_loader, include_repealed)
    except Exception as exc:
        # Do not print exception text: libraries can include request details.
        print(f"ERROR: statute subset build stopped ({type(exc).__name__}); check setup and dataset access.")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "statute_subset.jsonl"
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for section in sections:
            handle.write(json.dumps(section, ensure_ascii=False) + "\n")
    attribution = (
        "# Local statutory subset attribution\n\n"
        f"Dataset: [Open India Law]({DATASET_CARD}), compiled by Vaquill AI, licensed CC BY 4.0.\n\n"
        "The legislation text in this subset is sourced from India Code. This is a local, point-in-time "
        f"snapshot labelled `{SNAPSHOT}` (subset built {datetime.now(timezone.utc).date().isoformat()}). "
        "The excerpts are background material, not legal advice or an interpretation. Verify any source "
        "against the linked official source.\n"
    )
    (output_dir / "ATTRIBUTION.md").write_text(attribution, encoding="utf-8")

    counts: dict[str, int] = defaultdict(int)
    for section in sections:
        counts[section["title"]] += 1
    acts_found = 0
    acts_missing = 0
    for entry_index, entry in enumerate(entries):
        included_titles = [
            title for title in selected.get(entry_index, set())
            if counts.get(title, 0)
        ]
        if included_titles:
            acts_found += 1
            for title in sorted(included_titles, key=str.casefold):
                print(f"FOUND Act={title!r} sections={counts[title]}")
        else:
            acts_missing += 1
            print(f"MISSING Act={entry['name']!r} (no included sections)")
    print(
        f"FOUND/MISSING summary: acts_found={acts_found} acts_missing={acts_missing} "
        f"sections={len(sections)} output={output_path}"
    )
    return sections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--include-repealed",
        action="store_true",
        help="include rows excluded by the default in-force and repealed-title filters",
    )
    args = parser.parse_args(argv)
    try:
        build_subset(args.config, args.output_dir, args.include_repealed)
    except (OSError, ValueError, json.JSONDecodeError):
        print("ERROR: could not read the statute configuration or write the subset.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
