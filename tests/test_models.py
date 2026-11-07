"""Models M1-M4: quick training from the simulator, abstain, explanations, MILP priority, saved metrics.

Needs numpy, scikit-learn, lightgbm, scipy (requirements.txt); skipped where they are not installed.
"""
import json
import random
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("sklearn")
pytest.importorskip("lightgbm")
pytest.importorskip("scipy")

from orca.models import m4  # noqa: E402
from orca.models.features import FEATURES, window_features  # noqa: E402
from orca.models.m3 import ABSTAIN, LABELS  # noqa: E402
from orca.sim.engine import CLASSES, Simulator  # noqa: E402

METRICS = Path(__file__).resolve().parent.parent / "orca" / "models" / "metrics.json"


@pytest.fixture(scope="module")
def trained():
    from orca.models.train import train
    return train(quick=True, save=False)


def test_m3_has_eight_outputs_and_generalises(trained):
    models, metrics = trained
    assert LABELS == CLASSES + [ABSTAIN] and len(LABELS) == 8
    assert {"attack-gnss", "attack-signalling"} <= set(CLASSES)
    ho = metrics["M3"]["heldout_harder"]
    assert ho["accuracy_no_abstain"] > 0.85 and ho["selective_accuracy"] >= ho["accuracy_no_abstain"] - 1e-9
    assert len(ho["confusion_rows_true_cols_pred"]["matrix"]) == 7
    assert len(ho["confusion_rows_true_cols_pred"]["matrix"][0]) == 8


def test_m3_abstains_when_unsure_and_explains(trained):
    m3 = trained[0]["m3"]
    s = Simulator(11, sites=["CHN-03"])
    s.add("jamming", "CHN-03", start=2, j_over_n_db=12)
    hist = s.run(12)
    r = m3.classify(window_features(hist))
    assert r["label"] == "attack-jamming" and r["why"] and r["why"][0]["plain"]
    assert {w["feature"] for w in r["why"]} <= set(FEATURES)
    old = (m3.tau, m3.margin)
    m3.tau = 1.01                                   # nothing is that sure -> abstain
    try:
        r2 = m3.classify(window_features(hist))
        assert r2["label"] == ABSTAIN and r2["abstained"] and "human decides" in r2["note"]
    finally:
        m3.tau, m3.margin = old


def test_m3_weather_vs_jamming(trained):
    m3 = trained[0]["m3"]
    s = Simulator(12, sites=["CHN-05"])
    s.add("rain", "CHN-05", start=2, peak=60, ramp=2)
    assert m3.classify(window_features(s.run(12)))["label"] == "fault-weather"


def test_m1_low_false_alarms_and_flags_attacks(trained):
    models, metrics = trained
    ind = metrics["M1"]["in_distribution"]
    assert ind["ensemble_false_alarm_rate_normal"] < 0.03
    assert ind["auc_ecod"] > 0.8
    m1 = models["m1"]
    s = Simulator(13, sites=["CHN-02"])
    s.add("mgmt_intrusion", "CHN-02", start=2, wipe_at=3)
    x = np.asarray([window_features(s.run(10))])
    assert m1.flag(x)[0] and m1.explain(x[0])


def test_m2_interval_and_exposure(trained):
    models, metrics = trained
    m = metrics["M2_minute"]
    assert m["interval_p10_p90_coverage"] > 0.7 and m["mae_p50_failing_min"] < 20
    s = Simulator(14, sites=["CHN-01"])
    s.state["CHN-01"].battery_pct = 30
    s.add("power_cut", "CHN-01", start=1)
    f = models["m2"].forecast(s.run(15), "CHN-01")
    t = f["minutes_to_failure"]
    assert t["p10"] <= t["p50"] <= t["p90"] and f["cause"] == "power"
    assert "hospital" in f["exposure"] and "PB-15" in f["recommended"]


def test_m4_never_sheds_112_before_lower_priorities():
    rng = random.Random(3)
    for _ in range(40):
        demand = {s: {c: rng.randint(1, 30) for c in ("112", "hospital", "payments", "general")}
                  for s in ("CHN-01", "CHN-02")}
        cap = {s: rng.randint(5, 80) for s in demand}
        r = m4.allocate(demand, cap, {"GW": {"sites": list(demand), "mbps": rng.randint(10, 120)}})
        assert r["method"] == "milp"
        for s, a in r["allocation"].items():
            if a["112"]["served"] < 1:
                assert all(a[c]["granted_mbps"] == 0 for c in ("payments", "general")), (demand, cap, r)
            if a["hospital"]["served"] < 0.8:
                assert a["general"]["granted_mbps"] == 0


def test_m4_greedy_fallback_respects_capacity():
    r = m4.greedy({"CHN-01": {"112": 5, "general": 50}}, {"CHN-01": 20})
    a = r["allocation"]["CHN-01"]
    assert a["112"]["served"] == 1 and a["general"]["granted_mbps"] == 15


def test_saved_metrics_file():
    m = json.loads(METRICS.read_text())
    for k in ("M1", "M2_minute", "M3", "M4"):
        assert k in m
    pc = m["M3"]["heldout_harder"]["per_class"]
    assert set(pc) == set(CLASSES) and all("precision" in v and "recall" in v for v in pc.values())
    assert m["M4"]["112_fully_served"] is True


def test_detector_on_scenario_routes_model_alerts(trained):
    from orca.models.detector import Detector
    from orca.sim.scenario import ScenarioRun
    run = ScenarioRun("s3", detector=Detector(trained[0]))
    run.step_to(15)
    m3 = [a for a in run.model_alerts if a["source"] == "M3"]
    assert m3 and m3[0]["label"] == "attack-jamming" and m3[0]["site"] == "CHN-03"
    assert m3[0]["visible_to"] == ["satellite_operator"]          # EventFeed routing: roles that see source M3
    assert m3[0]["explain"]["why"]
    assert "satellite_operator" in run.released
