import datetime as dt

import pytest

from orca import rules
from orca.live.session import LiveSession
from orca.remediation import Refused


def test_global_manual_revokes_all_scoped_autonomy(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, "test-pin")
        session.autonomy("ASSISTED", ["CHN-01"], ["PB-10"], 20, "test-pin")
        assert session.rem.mode_for("PB-06", ["CHN-02"])[0] == "AUTO"
        assert session.rem.mode_for("PB-10", ["CHN-01"])[0] == "ASSISTED"

        session.autonomy("MANUAL", [], [], 20, "test-pin")
        assert session.rem.grants == []
        assert session.rem.mode_for("PB-06", ["CHN-02"])[0] == "MANUAL"
        assert session.rem.mode_for("PB-10", ["CHN-01"])[0] == "MANUAL"
    finally:
        session.close()


def test_scoped_manual_does_not_revoke_other_scopes(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, "test-pin")
        session.autonomy("AUTO", ["CHN-01"], ["PB-10"], 20, "test-pin")
        session.autonomy("MANUAL", ["CHN-02"], ["PB-06"], 20, "test-pin")
        assert session.rem.mode_for("PB-06", ["CHN-02"])[0] == "MANUAL"
        assert session.rem.mode_for("PB-10", ["CHN-01"])[0] == "AUTO"
    finally:
        session.close()


def test_global_manual_revokes_unused_auto_tokens_but_preserves_human_approval(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session.autonomy("AUTO", ["CHN-01"], ["PB-10"], 20, "test-pin")
        auto = session.rem.request_approval("mobile_operator", "PB-10", ["CHN-01"],
                                            {"message": "Emulated first notice"}, "test")
        human_plan = session.rem.request_approval("mobile_operator", "PB-10", ["CHN-01"],
                                                  {"message": "Emulated second notice"}, "test")
        human = session.rem.approve(human_plan["hash"], "commander", "test-pin")
        session.autonomy("MANUAL", [], [], 20, "test-pin")
        with pytest.raises(Refused, match="valid one-time approval token"):
            session.rem.execute("mobile_operator", "PB-10", ["CHN-01"], auto["params"], auto["auto_token"])
        assert session.rem.execute("mobile_operator", "PB-10", ["CHN-01"], human_plan["params"], human)["ok"]
    finally:
        session.close()


def test_scoped_manual_revokes_only_tokens_covered_by_removed_grant(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session.autonomy("AUTO", ["CHN-01"], ["PB-10"], 20, "test-pin")
        session.autonomy("AUTO", ["CHN-02"], ["PB-10"], 20, "test-pin")
        first = session.rem.request_approval("mobile_operator", "PB-10", ["CHN-01"],
                                             {"message": "Emulated first notice"}, "test")
        second = session.rem.request_approval("mobile_operator", "PB-10", ["CHN-02"],
                                              {"message": "Emulated second notice"}, "test")
        session.autonomy("MANUAL", ["CHN-01"], ["PB-10"], 20, "test-pin")
        with pytest.raises(Refused, match="valid one-time approval token"):
            session.rem.execute("mobile_operator", "PB-10", ["CHN-01"], first["params"], first["auto_token"])
        assert session.rem.execute("mobile_operator", "PB-10", ["CHN-02"], second["params"], second["auto_token"])["ok"]
    finally:
        session.close()


def test_auto_token_cannot_outlive_its_human_grant(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        grant = session.autonomy("AUTO", ["CHN-01"], ["PB-10"], 1, "test-pin")["grant"]
        plan = session.rem.request_approval("mobile_operator", "PB-10", ["CHN-01"],
                                            {"message": "Emulated notice"}, "test")
        assert plan["token_expires_at"] == grant["expires"]
        approval = next(e for e in session.world.audit.entries() if e["kind"] == "approved")
        assert approval["payload"]["token_expires_at"] == grant["expires"]
        session.world.facts["now"] = (rules.parse_ts(session.world.now) + dt.timedelta(minutes=2)).isoformat()
        with pytest.raises(Refused, match="approval expired"):
            session.rem.execute("mobile_operator", "PB-10", ["CHN-01"], plan["params"], plan["auto_token"])
    finally:
        session.close()
