# Documents and datasets

All checked-in sample agreements are fictional examples written for this repository. They are not drawn from real contracts, templates, or third-party datasets:

- `sample_docs/rental_agreement_sample.txt`
- `sample_docs/rental_agreement_sample.pdf` (reproducible with `python -m scripts.generate_sample_pdf`)
- `sample_docs/employment_agreement_sample.txt`
- `sample_docs/rental_vague_conflict_sample.txt`
- `sample_docs/prompt_injection_sample.txt`
- `sample_docs/employment_missing_terms_sample.txt`

No external document corpus is bundled or used for training. The app can optionally read a user-built local statutory subset from Open India Law for background retrieval; no dataset rows are checked in, and no dataset download occurs at runtime. See [DATA.md](DATA.md) for attribution and setup.
