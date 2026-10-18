# Optional statutory data

The optional statutory background feature uses a small local subset manually built from the `legislation` configuration of [Open India Law](https://huggingface.co/datasets/vaquill/open-india-law). The dataset is compiled by Vaquill AI and licensed under CC BY 4.0; its legislation records identify India Code as the source publisher. Consult the dataset page for its access conditions and current snapshot information.

The setup script writes selected, reassembled section text to `data/statutes/statute_subset.jsonl` and attribution to `data/statutes/ATTRIBUTION.md`. `data/statutes/` is ignored by Git: dataset rows are not included in this repository. The user selects which title matches to confirm in `config/statute_acts.json`. The script reports title ambiguities and does not silently choose among multiple title matches.

Every generated subset records the dataset snapshot label and build timestamp. The current script labels the dataset snapshot `v2026.08`. These records are point-in-time material; excerpts are displayed verbatim and are not interpretations. This feature is not legal advice.

The app reads the local JSONL at startup and uses its in-process BM25 index only. It does not download, refresh, or send data to Open India Law at runtime. Dataset judgments, Qdrant snapshots, and Voyage embeddings are not used. See [NETWORK.md](NETWORK.md), [LIMITATIONS.md](LIMITATIONS.md), and the [dataset page](https://huggingface.co/datasets/vaquill/open-india-law).

## Recommended legal reference source

For Indian statutory text, use **India Code** as the source of truth when reviewing, updating, or replacing the local subset. The current Open India Law subset is a practical structured starting point because its records identify India Code as the legislation source; it is still a third-party compilation and may be incomplete or out of date. Verify each Act, section, amendment/effective date, and applicable state against the official source before adding it to a release subset. Preserve the official source URL and snapshot/provenance metadata, and check the source's current access and reuse terms.

This corpus is retrieval context for the local LLM, not knowledge-training data: the app retrieves a few mapped sections and supplies them alongside (not as part of) the agreement evidence. Avoid importing a broad, unreviewed legal corpus. Court judgments are a separate kind of reference and should be added only if case-law search becomes an explicit feature, with court, citation, date, status, and source provenance maintained separately.
