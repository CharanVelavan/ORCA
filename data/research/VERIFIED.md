# What was checked in the Codex research reports (7 Nov 2026)

Reports 01–03 were written by Codex (gpt-6-luna, web search, read-only). They are inputs, not
sources. Before anything goes into DATA_CARD.md it is checked here.

## Corrected

| Item | Report said | Official value | Checked against |
|---|---|---|---|
| P.838-3 7 GHz alpha_H | 1.40 | 1.4810 | ITU-R P.838-3 PDF (sha256 3ab74829…) |
| P.838-3 12 GHz k_H / alpha_H | 0.0188 / 1.22 | 0.02386 / 1.1825 | same |
| P.838-3 38 GHz k_H | 0.443 | 0.4001 | same |
| Turkcell schema | "NOT FOUND" | read from the archive, see below | Turkcell GitHub archive, Region A |

The generator reads `data/itu_p838_3_coefficients.csv` (115 frequencies, 1–900 GHz,
extracted from the official PDF), never hand-typed coefficients.

## Turkcell Region A (ITU AI/ML in 5G Challenge 2021), from the archive itself

- `rl-kpis.tsv`: 1,992,986 **daily** rows, 2018-12-31 to 2020-12-25, 3,465 links, 1,674 sites.
  Columns: type (vendor ENK/NEC), datetime, tip, mlid, mw_connection_no, site_id, card_type,
  adaptive_modulation, freq_band (anonymised f1–f5), severaly_error_second, error_second,
  unavail_second, avail_time, bbe, rxlevmax, capacity, modulation, rlf.
- `rlf` positives: 1,219 (0.061%).
- `met-real.tsv`: 479,241 hourly rows from 20 stations (Turkey), columns temp, temp_max, temp_min,
  wind_dir, wind_speed, wind_dir_max, wind_speed_max, humidity, precipitation,
  precipitation_coeff, pressure, pressure_sea_level. Contains sensor errors (temp 298,
  pressure 10,211): clean before use.
- `met-forecast.tsv`: 5-day forecasts; `rl-sites.tsv`, `met-stations.tsv`: height and clutter
  class; `distances.tsv`: station-to-site distances.

**Consequence:** Turkcell can calibrate *daily* link-failure risk against weather (M2's horizon)
and the fault side of M3. It cannot calibrate 10-second telemetry or Chennai's climate; those
come from physics (P.838, P.530, P.618) plus stated assumptions.

## Not yet checked (spot-check before citing in the report)

- Viasat KA-SAT timings (03:02 UTC, 04:15 UTC, ~45 min) — report 02.
- MITRE ATT&CK ICS ids T1692 / T1695, and ITU-T Q.3066 (2026) — report 02.
- Chennai flood-system figures (117 rain gauges, 74 watersheds) — report 03.
- Tamil Nadu 112 call volumes (tn.data.gov.in) and NPCI statistics — report 01.
- Chennai R0.01 from the ITU-R P.837 digital map: still to extract.
