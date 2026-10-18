from src.verify import verify_clause_quote, pass_rate


def test_verify_quote_match():
    clause = "This agreement shall continue for twelve months. The tenant shall pay rent monthly."
    quote = "The tenant shall pay rent monthly."
    result = verify_clause_quote("p1-c001", clause, quote)
    assert result.match_found is True
    assert result.start_offset is not None


def test_verify_quote_mismatch():
    clause = "The tenant shall pay rent monthly."
    quote = "The tenant shall pay rent annually."
    result = verify_clause_quote("p1-c001", clause, quote)
    assert result.match_found is False


def test_quote_offsets_point_into_original_text_after_whitespace_normalisation():
    clause = "The TENANT \n shall pay rent."
    result = verify_clause_quote("p1-c001", clause, "tenant shall")
    assert result.match_found is True
    assert clause[result.start_offset:result.end_offset] == "TENANT \n shall"


def test_pass_rate_counts():
    verified = [
        verify_clause_quote("a", "The tenant pays rent.", "The tenant pays rent."),
        verify_clause_quote("b", "The tenant pays rent.", "The tenant pays annually."),
    ]
    summary = pass_rate(verified)
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
