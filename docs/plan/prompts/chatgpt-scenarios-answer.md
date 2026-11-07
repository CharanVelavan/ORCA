# ChatGPT's scenario answer (8 Nov 2026), saved as input for agent G-B

Saved by Claude from the user's paste, with prose shortened; timelines, verdicts, models, playbooks, heal
targets and risks are kept. **Corrections that override this text** are in `scenarios/SCHEMA.md` and the
G-B prompt (verdict for 03/04 is AMBIGUITY; GAP-01 via clocks; PB-10 owner = mobile operator; tower backhaul
modems in S1; PB-05 vs PB-06 CONFLICT belongs in S1 and N4, not S2). Percentages are targets only.

General: M3 has no overload class (benign overload = `normal`, or abstain). M4 always raises GAP-IN-03; the
commander gives a temporary priority, never presented as law. Executable: PB-01, PB-06, PB-10. All failover
on Indian gateways; foreign proposals blocked.

## S1 - The night Chennai's satellite terminals disappear (attack, management plane; gaps 09, 01, 02)
Story: a stolen management login sends destructive commands to emulated satellite terminals; 112 and payments fail.
Cause: exposed VPN account -> satellite management -> terminal-wipe commands. M3 = attack-management-plane (SHAP: login and command anomalies).
Timeline: T+00 M1 unusual VPN login · T+04 Satellite Operator finds exposed access · T+08 M3 management-plane indicators · T+12 Gap Analyst GAP-IN-09 · T+18 Satellite Operator sees wipe commands · T+24 Mobile Operator sees failing transactions · T+30 CERT-In agent maps clocks, GAP-IN-01 · T+36 Gap Analyst GAP-IN-02 · T+43 Commander approves PB-01 and PB-10 · T+55 Mobile Operator tests, gets approval for PB-06 · T+78 M1 verifies recovery on unaffected paths.
Impact: 112 failures, shops lose UPI, some hospital links unreachable from T+24.
Verdicts: T+12 GAP-09 · T+30 GAP-01 · T+36 GAP-02 · T+55 COMPLIANT Rule 60(1)(b) if Indian gateway.
Models: M1 (VPN logins, command frequency), M3 (commands, sessions).
Playbooks: PB-01 (satellite operator), PB-10, PB-06 (mobile operator, independently checked clean path). PB-04 specified only.
Heal target: critical-service success 42% -> 95%. Wiped terminals stay damaged.
Human decisions: authorise account isolation despite disruption; when to warn; approve only a verified backup.
Rules off: recovery may skip gateway location; agents miss clock differences and dependants.
Data: VPN sessions, login failures, privilege changes, mgmt commands, terminal availability, txn success, gateway country, route integrity, report timestamps.
Demo 110 s. Risks: KA-SAT is inspiration, not a Chennai incident; terminal restoration not implemented; NEEDS CHECK which paths preserve service after wipes.

## S2 - A storm leaves Chennai fighting for capacity (weather fault; gaps 03, 04)
Story: NE-monsoon rain fade cuts emulated satellite capacity; 112, hospital, grid and payments compete.
Cause: rain fade + high traffic. M3 = fault-weather (not attack-jamming); a high-load segment may be `normal`.
Timeline: T+00 M1 rising traffic and loss · T+07 M2 forecasts reduced margin · T+13 M3 weather degradation · T+21 M2 predicts battery exhaustion at a site · T+25 GAP-IN-04 · T+32 M4 requests priority rules, GAP-IN-03 · T+40 operators disagree PB-06 vs PB-05 · T+47 Commander rejects containment without attack evidence · T+59 Mobile Operator executes PB-06 · T+76 PB-10 warns dependants · T+94 M1 verifies critical delivery.
Impact: some 112 fail, hospital transfers slow, grid and payments compete from T+21.
Verdicts: T+25 GAP-04 · T+32 GAP-03 · T+59 COMPLIANT domestic gateway.
Models: M1 (utilisation, loss), M2 (rain, margin, battery, minutes to outage), M3 (radio + security), M4 (capacity, demand).
Playbooks: PB-06, PB-10; PB-05 considered not executed; PB-09 specified.
Heal target: critical-traffic delivery 68% -> 97%; general traffic may stay degraded.
Human decisions: a temporary priority order (112, hospitals, grid, payments), not law.
Rules off: M4 quietly uses an arbitrary order; false attack assumption -> needless isolation.
Demo 105 s. Risks: storm vs jamming must be distinguishable.

## S3 - The cell that heals itself without trusting the backup (attack, jamming; gaps 08, 06)
Story: jamming on one emulated backhaul link; ORCA refuses an unverified backup, checks another route, restores the cell.
M3 = attack-jamming.
Timeline: T+00 M1 abrupt loss · T+06 M2 forecasts primary failure · T+12 M3 jamming · T+19 Mobile Operator proposes path A · T+24 Satellite Operator: path A unverified · T+28 GAP-IN-08 · T+34 GAP-IN-06 · T+42 path B verified, Indian gateway · T+50 Commander approves PB-06 · T+68 M1 confirms recovery.
Impact: failed 112, delayed UPI, intermittent connectivity from T+06.
Verdicts: T+28 GAP-08 · T+34 GAP-06 · T+42 COMPLIANT 60(1)(b).
Heal target: packet loss 40% -> 3%; route trace shows Indian gateway. Path failover, not beam hopping.
Human decisions: accept a slower clean route; reject path A.
Rules off: controller picks the first backup = the trap path.
Demo 90 s. Risks: clean-path test criteria NEEDS CHECK.

## N1 - Hospital corridor battery cliff (power fault; gaps 04, 02)
Mains failure at a site; battery drains; hospital and 112 comms unreliable. M3 = fault-power/equipment.
Timeline: T+00 Power Utility reports supply failure · T+07 M1 rising loss · T+14 M2 predicts 20 min battery · T+20 M3 power fault · T+25 GAP-04 · T+29 GAP-02 · T+36 Commander approves PB-10 and PB-06 testing · T+48 Mobile Operator executes failover · T+66 M1 confirms restored service.
Heal target: service success 54% -> 98%. Demo 75 s.

## N2 - Payments disappear, but nobody gets warned (configuration fault; gap 02)
A maintenance change breaks routing; UPI and ATMs fail. M3 = fault-power/equipment (non-malicious).
Timeline: T+00 maintenance error · T+07 M1 payment loss · T+12 M3 non-attack fault · T+20 Mobile Operator confirms failures · T+26 GAP-02 · T+35 faulty route found · T+43 PB-10 approved · T+50 PB-06 clean failover · T+73 recovery verified.
ChatGPT says no GAP-01 for an ordinary fault - NEEDS CHECK against the TCSR "security incident" definition.
Heal target: payment success 30% -> 97%. Demo 70 s.

## N3 - The invisible weakness in a feeder link (audit inject; gaps 06, 09)
Judge injects an audit: an emulated feeder link carries test traffic unprotected; no outage. M3 = abstain.
Timeline: T+00 judge inject · T+06 Satellite Operator checks · T+12 M1 normal performance · T+18 M3 abstains · T+23 GAP-06 · T+29 GAP-09 · T+36 Commander evaluates routing · T+44 Mobile Operator tests protected domestic backup · T+57 PB-06 approved if checks pass · T+74 exposed path unused.
Heal target: traffic on exposed route 100% -> 0% (avoidance, not repair). Demo 90 s.
Risk: passive interception is not detectable by telemetry; it must be an injected audit.

## N4 - The network dashboard lies (telemetry manipulation; gaps 09, 08, 02)
Attacker edits management telemetry: dashboard green, 112 failing. M3 = attack-management-plane.
Timeline: T+00 unauthorised telemetry change · T+08 M1 reported health vs measured loss disagree · T+14 M3 · T+20 GAP-09 · T+27 path A proposed · T+31 GAP-08 · T+38 GAP-02 · T+47 PB-01 and PB-10 approved · T+56 PB-06 via verified path B · T+72 M1 confirms recovery from independent telemetry.
Heal target: 112 success 35% -> 98%. Demo 105 s. Needs two independent evidence sources.

## N5 - One incident, several reporting clocks (cross-operator; gaps 01, 09, 02)
One management intrusion hits telecom and grid comms; each organisation learns at a different time. M3 = attack-management-plane.
Timeline: T+00 M1 suspicious management activity · T+05 Satellite Operator notices · T+12 M3 · T+18 Power Utility loses grid telemetry · T+24 Mobile Operator sees 112 disruption · T+28 CERT-In agent compares clocks, GAP-01 · T+35 GAP-09 · T+41 GAP-02 · T+48 PB-01 and PB-10 approved · T+64 PB-06 · T+82 recovery verified.
CERT-In negative controls COMPLIANT where reporting, contact and logs are satisfied.
Heal target: critical-message success 55% -> 96%. Demo 100 s. Do not claim all four reports are always mandatory.

## CAP - Chennai's double crisis (weather + intrusion; all 7 gaps)
Two independent causes: monsoon rain fade (M2) and a management intrusion (M3 = attack-management-plane). M3 must not blame the rain on the attacker.
Timeline: T+00 rain fade, capacity falls (M2) · T+08 anomalous mgmt login, GAP-09 · T+17 M3 attack confirmed · T+26 GAP-06 · T+37 battery falls, GAP-04 · T+48 path A unverified, GAP-08 · T+57 M4 cannot serve all, GAP-03 · T+68 Power Utility: dependants need warning, GAP-02 · T+80 CERT-In maps clocks, GAP-01 · T+94 PB-01 and PB-10 approved · T+112 PB-06 via clean path B, Indian gateway (COMPLIANT) · T+154 recovery validated, audit and recommendations done.
Heal targets: critical-service success 43% -> 97%; packet loss 38% -> 3%. Demo 120 s.
A missing rule must never become a VIOLATION. A foreign-gateway proposal is rejected without executing.

## ChatGPT's ranking of N1-N5
1 N4 false-green · 2 N1 battery · 3 N5 clocks · 4 N3 feeder · 5 N2 payments. (User decision 8 Nov: implement all five.)
