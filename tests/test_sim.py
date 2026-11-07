"""Simulator: determinism, physics, labels, progressive release via EventFeed, clean-path check, health hook."""
import pytest

from orca.agents import EventFeed, load_agent_roles
from orca.remediation import Refused, Remediation
from orca.sim import netops, physics
from orca.sim.engine import CLASS_OF, Simulator
from orca.sim.netstate import NetState
from orca.sim.scenario import ScenarioRun, load_scenario
from orca.sim.topology import LINK_CLASSES
from orca.scanner import scan
from orca.world import World

NOW = "2026-11-10T19:30:00+05:30"


def test_deterministic_with_seed():
    def run(seed):
        s = Simulator(seed)
        s.add("rain", "CHN-05", start=3, peak=40)
        s.add("jamming", "CHN-03", start=5, j_over_n_db=10)
        return s.run(20)
    assert run(5) == run(5)
    assert run(5) != run(6)


def test_p838_from_csv_and_fade_monotonic():
    kh, ah, kv, av = physics.p838_coefficients(12.0)
    assert (kh, ah, kv, av) == (0.02386, 1.1825, 0.02455, 1.1216)     # Table 5 row, read from the CSV
    lo, mid, hi = physics.p838_coefficients(10)[0], physics.p838_coefficients(11.5)[0], physics.p838_coefficients(12)[0]
    assert lo < mid < hi
    fades = [physics.rain_fade_db(LINK_CLASSES["satellite"], r) for r in (0, 5, 20, 45, 90)]
    assert fades[0] == 0 and fades == sorted(fades)
    assert physics.rain_fade_db(LINK_CLASSES["fibre"], 100) == 0


def test_jamming_raises_noise_rain_lowers_received_level():
    s = Simulator(1, sites=["CHN-01", "CHN-02"])
    s.add("jamming", "CHN-01", start=0, j_over_n_db=12)
    s.add("rain", "CHN-02", start=0, peak=60, ramp=1)
    recs = s.run(6)[-2:]
    jam, rain = recs
    assert jam["noise_rise_db"] > 10 and abs(jam["rx_dbm"] - LINK_CLASSES["satellite"]["rx_dbm"]) < 2
    assert rain["noise_rise_db"] < 1 and rain["rx_dbm"] < LINK_CLASSES["satellite"]["rx_dbm"] - 5
    assert rain["expected_fade_db"] > 5 and abs(rain["fade_residual_db"]) < 3


@pytest.mark.parametrize("kind", sorted(CLASS_OF))
def test_every_condition_has_its_label(kind):
    s = Simulator(2, sites=["CHN-01"])
    params = {"gateway": "GW-IN-1"} if kind == "gateway_power" else {}
    s.add(kind, None if kind == "gateway_power" else "CHN-01", start=2, **params)
    recs = s.run(6)
    assert recs[0]["label"] == "normal" and recs[-1]["label"] == CLASS_OF[kind]


def test_ka_sat_chain_wipes_terminals_and_containment_ends_it():
    s = Simulator(3, sites=["CHN-02"])
    s.add("mgmt_intrusion", "CHN-02", start=1, wipe_at=4)
    recs = s.run(10)
    assert recs[1]["mgmt_login_anomalous"] == 1
    assert sum(r["mgmt_wipe"] for r in recs) > 0 and recs[-1]["terminals_up"] == 0 and recs[-1]["packet_loss"] > 0.9
    s.mgmt_contained = True
    assert s.step()[0]["label"] == "normal"


def test_scenario_release_is_progressive_and_uses_eventfeed_routing():
    sc = load_scenario("s1")
    run = ScenarioRun(sc)
    out = run.step_to(5)
    feed = EventFeed(sc, load_agent_roles())
    assert set(out) == set(feed.route(sc["events"][0]))          # t=0 vpn_login -> satellite_operator only
    assert "mobile_operator" not in out
    assert all(a["t"] <= 5 for al in out.values() for a in al)
    out2 = run.step_to(30)
    assert "mobile_operator" in out2 and all(5 < a["t"] <= 30 for al in out2.values() for a in al)
    assert run.measured("CHN-02", "terminals_up", 25) == 0
    assert run.measured("CHN-02", "mgmt_wipe", 18) >= 12


def test_scenario_with_world_merges_facts_and_routes(tmp_path):
    w = World.new({"jurisdiction": "IN"}, tmp_path / "a.jsonl")
    run = ScenarioRun("s3", world=w)
    run.step_to(45)
    assert w.routes["CHN-03"]["A"]["integrity"] == "failed"
    assert w.routes["CHN-03"]["C"]["gateway"] == "GW-XX"
    assert w.facts["now"].startswith("2026-11-10T19:42")
    assert any(a.get("visible_to") for a in w.alerts)
    assert run.measured("CHN-03", "noise_rise_db", 10) > 3       # jamming inferred from the scenario


def test_clean_path_check_blocks_failed_foreign_and_jammed_paths():
    run = ScenarioRun("s3")
    run.step_to(45)
    net = NetState.load()
    chk = lambda p: netops.check_path_clean("CHN-03", p, net, run.sim)  # noqa: E731
    assert not chk("A")["clean"] and chk("A")["integrity"] == "failed"          # failed is never upgraded
    c = chk("C")
    assert not c["clean"] and any(x["check"].startswith("gateway in India") and not x["ok"] for x in c["checks"])
    assert chk("B")["clean"] and chk("B")["integrity"] == "verified"


def test_backup_satellite_path_not_clean_while_mgmt_intrusion_uncontained():
    s = Simulator(4, sites=["CHN-05"])
    s.add("mgmt_intrusion", "CHN-05", start=0)
    s.run(3)
    net = NetState.load()
    r = netops.check_path_clean("CHN-05", "B", net, s)
    assert not r["clean"] and any(x["check"] == "management plane not compromised" and not x["ok"] for x in r["checks"])
    s.mgmt_contained = True
    assert netops.check_path_clean("CHN-05", "B", net, s)["clean"]


def test_failover_heals_packet_loss():
    run = ScenarioRun("s3")
    run.step_to(45)
    assert run.measured("CHN-03", "packet_loss", 45) > 0.3
    net = NetState.load()
    p = netops.apply_playbook(net, "PB-06", ["CHN-03"], params={"path": "B"}, sim=run.sim)
    assert "active_path: B" in p.diff and "failover_allowed: false" in p.diff
    run.sim.run(3)
    assert run.sim.site_history("CHN-03")[-1]["packet_loss"] < 0.1


# ------------------------------------------------------------------ integration with the lead's remediation
def _world(tmp_path):
    w = World.new({"jurisdiction": "IN", "now": NOW}, tmp_path / "audit.jsonl")
    sim = Simulator(9)
    ops = netops.attach(w, NetState.load(), sim)
    return w, sim, ops


def test_remediation_executes_patch_through_health_hook(tmp_path):
    w, sim, ops = _world(tmp_path)
    rem = Remediation(w)
    plan = rem.request_approval("satellite_operator", "PB-12", ["SAT-MGMT"], {}, "close exposed VPN")
    tok = rem.approve(plan["hash"], "commander", "1234")
    res = rem.execute("satellite_operator", "PB-12", ["SAT-MGMT"], {}, tok)
    assert res["ok"] and [s["pct"] for s in res["stages"]] == [5, 25, 100]
    assert not [f for f in scan(ops.net) if f.check in ("SCN-VPN-EXPOSED", "SCN-MGMT-EXPOSED")]
    v = next(r for r in ops.records if r["event"] == "verified")
    assert v["ok"] and v["reattack"][0]["succeeded"] is False and sim.mgmt_contained


def test_failed_stage_rolls_back_config(tmp_path):
    w, sim, ops = _world(tmp_path)
    before = ops.net.text("SAT-MGMT")
    rem = Remediation(w)
    params = {"simulate_failure_at": 25}
    plan = rem.request_approval("satellite_operator", "PB-11", ["SAT-MGMT"], params, "rotate")
    res = rem.execute("satellite_operator", "PB-11", ["SAT-MGMT"], params, rem.approve(plan["hash"], "c", "1"))
    assert not res["ok"] and res["stages"][-1] == {"pct": 25, "healthy": False}
    assert ops.net.text("SAT-MGMT") == before
    assert ops.records[-1]["event"] == "rolled_back"


def test_pb06_to_foreign_gateway_is_refused(tmp_path):
    w, sim, ops = _world(tmp_path)
    w.routes = {"CHN-03": {"C": {"gateway": "GW-XX", "integrity": "verified"}}}
    rem = Remediation(w)
    plan = rem.request_approval("mobile_operator", "PB-06", ["CHN-03"], {"path": "C"}, "failover")
    assert not plan["clone_test"]["passed"] and "India" in plan["clone_test"]["detail"]   # with or without the lead patch
    with pytest.raises(netops.PatchRefused):
        netops.apply_playbook(ops.net, "PB-06", ["CHN-03"], params={"path": "C"},
                              sim=_sim_with_route("CHN-03", "C", "GW-XX"))


def _sim_with_route(site, path, gw):
    s = Simulator(1, sites=[site])
    s.offer_route(site, path, gw, "verified")
    s.run(1)
    return s


def test_netops_clone_test_changes_nothing():
    net, sim = NetState.load(), Simulator(1)
    before = net.text("SAT-MGMT")
    r = netops.clone_test(net, "PB-12", ["SAT-MGMT"], {}, sim)
    assert r["passed"] and "exposure: restricted" in r["diff"]
    assert net.text("SAT-MGMT") == before and not sim.mgmt_contained


def test_all_scenarios_simulate_without_error():
    for name in ("s0", "s1", "s2", "s3", "n1", "n2", "n3", "n4", "n5", "cap"):
        run = ScenarioRun(name)
        run.run(extra=2)
        assert run.sim.history
