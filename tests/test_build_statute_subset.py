import json

from scripts import build_statute_subset as builder


def row(**updates):
    value = {
        "act_id": "TEST_fixture_00001",
        "chunk_id": "TEST_central_1_s001_1",
        "title": "Example Employment Fixture Act",
        "chapter": "",
        "section_number": "1",
        "section_title": "Synthetic fixture section",
        "text": "Act: Synthetic fixture header\nSynthetic fixture content.",
        "state": "",
        "act_status": "in_force",
        "in_force": True,
        "year": 2020.0,
        "source_url": "https://example.test/source",
        "mirror_url": "",
        "source_publisher": "Synthetic fixture",
    }
    value.update(updates)
    return value


def config(path, **entry_updates):
    entry = {
        "name": "Synthetic example act",
        "title_patterns": ["Example Employment Act"],
        "state": "central",
        "scope": "employment",
    }
    entry.update(entry_updates)
    path.write_text(json.dumps([entry]), encoding="utf-8")
    return path


def test_title_matching_is_case_insensitive_partial_and_tolerates_typo():
    assert builder._title_matches(
        "THE Industrial Employmnet (Standing Orders) Fixture Act, 1946",
        "industrial employment standing orders",
    )
    assert builder._title_matches("The Example Employment Fixture Act", "example employment")
    assert not builder._title_matches("An unrelated fixture", "example employment")


def test_stream_build_reassembles_chunks_strips_headers_and_filters_repealed(tmp_path, capsys):
    config_path = config(tmp_path / "config.json")
    rows = [
        row(chunk_id="TEST_central_1_s001_2", text="Act: Header\nsecond synthetic part."),
        row(chunk_id="TEST_central_1_s001_1", text="Act: Header\nfirst synthetic part."),
        row(
            act_id="TEST_fixture_repealed",
            chunk_id="TEST_central_1_s002_1",
            section_number="2",
            act_status="repealed",
            in_force=False,
            text="Act: Header\nrepealed synthetic part.",
        ),
        row(
            act_id="TEST_fixture_title_repealed",
            title="Example Employment Fixture Act, Rep.,",
            chunk_id="TEST_central_1_s003_1",
            section_number="3",
            text="Act: Header\ntitle-marked repealed synthetic part.",
        ),
    ]
    output_dir = tmp_path / "statutes"
    sections = builder.build_subset(config_path, output_dir, loader=lambda: iter(rows))
    assert len(sections) == 1
    section = sections[0]
    assert section["state"] == "central"
    assert section["year"] == 2020
    assert section["text"] == "first synthetic part.\n\nsecond synthetic part."
    assert "Act:" not in section["text"]
    assert section["source_url"] == "https://example.test/source"
    assert sections == [json.loads((output_dir / "statute_subset.jsonl").read_text().splitlines()[0])]
    assert (output_dir / "ATTRIBUTION.md").is_file()
    output = capsys.readouterr().out
    assert "COLUMNS:" in output
    assert "FOUND Act='Example Employment Fixture Act' sections=1" in output


def test_title_ambiguity_only_includes_exactly_confirmed_title(tmp_path):
    config_path = config(
        tmp_path / "config.json",
        title_patterns=["Example Employment Act"],
        exact_titles=["Example Employment Fixture Act"],
    )
    rows = [
        row(act_id="TEST_fixture_confirmed"),
        row(act_id="TEST_fixture_other", title="Example Employmnet Fixture Act"),
    ]
    sections = builder.build_subset(
        config_path,
        tmp_path / "out",
        loader=lambda: iter(rows),
    )
    assert [item["act_id"] for item in sections] == ["TEST_fixture_confirmed"]


def test_schema_mismatch_and_missing_act_report_and_continue(tmp_path, capsys):
    config_path = config(
        tmp_path / "config.json",
        title_patterns=["Missing Synthetic Act"],
    )
    sections = builder.build_subset(
        config_path,
        tmp_path / "out",
        loader=lambda: iter([{"title": "Unrelated fixture", "state": ""}]),
    )
    assert sections == []
    output = capsys.readouterr().out
    assert "COLUMNS: state, title" in output
    assert "MISSING pattern='Missing Synthetic Act'" in output
    assert "MISSING Act='Synthetic example act'" in output


def test_matched_title_with_missing_optional_columns_fails_gracefully(tmp_path, capsys):
    config_path = config(
        tmp_path / "config.json",
        title_patterns=["Example Employment Act"],
    )
    sections = builder.build_subset(
        config_path,
        tmp_path / "out",
        loader=lambda: iter([{"title": "Example Employment Fixture Act", "state": ""}]),
    )
    assert sections == []
    output = capsys.readouterr().out
    assert "COLUMNS: state, title" in output
    assert "MATCH pattern='Example Employment Act'" in output
    assert "MISSING Act='Synthetic example act'" in output
