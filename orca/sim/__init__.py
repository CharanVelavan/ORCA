"""Emulated Chennai NTN network (everything simulated; no real network or device is touched).

engine (minute-step simulator, conditions, labels) · physics (ITU-R P.838-3 rain fade, jamming SINR) ·
topology (6 sites, GW-IN-1/2, forbidden GW-XX) · scenario (scenario files -> simulator, progressive
release via agents.EventFeed) · netstate (netconfig/ as code, diffs) · netops (patch/heal playbooks:
apply, verify, rollback, clean-path check, World.health hook) · attacks (re-attack tests) · dataset
(training episodes). See docs/NETWORK.md.
"""
