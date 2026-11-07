import datetime as dt

from orca import kb as kbmod


def test_kb_is_valid():
    kb = kbmod.load()
    assert kbmod.validate(kb) == []


def test_three_six_hour_clocks_have_different_triggers():
    kb = kbmod.load()
    certin = kb.records["IN-CERTIN-DIR-2022-ii"]["obligation"]
    dot = kb.records["IN-TCSR-2024-R7-1"]["obligation"]
    assert certin["deadline"] == dot["deadline"] == "PT6H"
    assert certin["trigger"] == "noticing" and dot["trigger"] == "occurrence"


def test_dpdp_breach_clock_not_in_force_today():
    kb = kbmod.load()
    assert not kb.in_force("IN-DPDP-RULES-2025-R7", dt.date(2026, 11, 10))
    assert kb.in_force("IN-DPDP-RULES-2025-R7", dt.date(2027, 6, 1))
