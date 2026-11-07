import json

from orca.audit import GENESIS, AuditLog


def make(tmp_path, n=4):
    log = AuditLog(tmp_path / "audit.jsonl")
    for i in range(n):
        log.append("verdict", "rule_engine", {"i": i, "text": "naïve ✓"}, f"2026-11-10T19:0{i}:00+05:30")
    return log


def lines(log):
    return log.path.read_text(encoding="utf-8").splitlines()


def test_append_and_verify(tmp_path):
    log = make(tmp_path)
    es = log.entries()
    assert [e["seq"] for e in es] == [1, 2, 3, 4]
    assert es[0]["prev_hash"] == GENESIS
    assert es[1]["prev_hash"] == es[0]["hash"]
    assert log.verify() is None
    # reopening the file continues the same chain
    again = AuditLog(log.path)
    e5 = again.append("approval", "human", {"ok": True}, "2026-11-10T20:00:00+05:30")
    assert e5["seq"] == 5 and e5["prev_hash"] == es[-1]["hash"]
    assert again.verify() is None


def test_empty_log_verifies(tmp_path):
    assert AuditLog(tmp_path / "a.jsonl").verify() is None


def test_edit_payload_detected(tmp_path):
    log = make(tmp_path)
    ls = lines(log)
    e = json.loads(ls[1])
    e["payload"]["i"] = 99
    ls[1] = json.dumps(e)
    log.path.write_text("\n".join(ls) + "\n", encoding="utf-8")
    assert log.verify() == 2


def test_delete_line_detected(tmp_path):
    log = make(tmp_path)
    ls = lines(log)
    del ls[1]
    log.path.write_text("\n".join(ls) + "\n", encoding="utf-8")
    # the line now in position 2 still says seq 3
    assert log.verify() == 2


def test_delete_last_line_is_not_detected_but_documented(tmp_path):
    # Tamper-evident, not tamper-proof: dropping the tail leaves a valid shorter chain.
    log = make(tmp_path)
    ls = lines(log)[:-1]
    log.path.write_text("\n".join(ls) + "\n", encoding="utf-8")
    assert log.verify() is None


def test_reorder_detected(tmp_path):
    log = make(tmp_path)
    ls = lines(log)
    ls[1], ls[2] = ls[2], ls[1]
    log.path.write_text("\n".join(ls) + "\n", encoding="utf-8")
    assert log.verify() == 2


def test_garbage_line_detected(tmp_path):
    log = make(tmp_path)
    ls = lines(log)
    ls[2] = "not json"
    log.path.write_text("\n".join(ls) + "\n", encoding="utf-8")
    assert log.verify() == 3
