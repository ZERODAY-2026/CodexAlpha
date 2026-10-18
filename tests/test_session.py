from src.session import SessionStore


def test_sessions_use_random_ids_and_expire_in_memory():
    store = SessionStore(ttl_seconds=60)
    first = store.create("one.txt")
    second = store.create("two.txt")
    assert first.session_id != second.session_id
    assert store.get(first.session_id) is first
    assert store.delete(first.session_id) is True
    assert store.get(first.session_id) is None


def test_expired_session_is_unavailable():
    store = SessionStore(ttl_seconds=0)
    record = store.create("expired.txt")
    assert store.get(record.session_id) is None
