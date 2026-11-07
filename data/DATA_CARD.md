# ORCA-NTN synthetic dataset: data card (DRAFT v0, 7 Nov 2026)

Emulated data for a satellite-backed network in **Chennai, India** (main city), during the
northeast monsoon. Value sources: **physics** (standard model), **calibrated** (fitted to the
real ITU sandbox Turkcell radio-link-failure data), **assumed** (our stated parameter).
Nothing here is an official statistic.

## Tables
1. **sites** (static): site_id, site_type (macro tower, small cell, ATM cluster, bank branch,
   hospital, 112 call centre, water pumping, temporary event cell), zone (T. Nagar, Adyar,
   Velachery, Anna Nagar, Guindy, OMR, Royapuram port, Chepauk, Tambaram), lat/lon/elevation,
   backhaul primary/secondary/backup (fibre / microwave / satellite), mw_freq_GHz, mw_path_km,
   polarisation, sat_band (Ku/Ka), sat_freq_GHz, gateway_id, battery_kWh, typical_load_kW,
   genset, criticality_tier (1=112, 2=hospital, 3=water, 4=payments, 5=rest), dependents.
   About 50 urban sites, 2 gateways, 1 management network.
2. **link telemetry** (10 s): rx_level_dBm, tx_power_dBm, noise_floor_dBm, snr_dB, sinr_dB, ber,
   errored_s, severely_errored_s, unavailable_s, modulation, capacity_Mbps, throughput_Mbps,
   latency_ms, jitter_ms, packet_loss_pct, link_state, active_path, expected_fade_dB
   (ITU-R P.838), fade_residual_dB.
3. **weather** (1 min, per zone): rain_rate_mm_h, temp_C, humidity_pct, wind_ms, gust_ms,
   pressure_hPa, flood_depth_cm, cyclone_flag, lightning_flag.
4. **power** (1 min, per site): grid_on, genset_on, battery_soc_pct, battery_temp_C, load_kW,
   hours_left.
5. **services** (1 min, per zone): calls_per_min, emergency_112_per_min, card_txn_per_min,
   atm_txn_per_min, txn_failed_pct, data_GB, active_users, event_flag (Deepavali, Pongal,
   payday, cricket at Chepauk).
6. **management-plane logs** (per event): session_id, user, src_ip_pseudo, src_category,
   auth_method, vpn_endpoint, login_hour, command_type (show/config/firmware_push/reboot/wipe),
   target_count, success, config_hash vs baseline (drift).
7. **satellite gateway** (1 min): carrier_CN_dB, uplink_power_dBW, beam_load_pct,
   interference_report, sun_outage_flag.
8. **labels** (per event): event_id, scenario_id, class (normal, fault-weather,
   fault-equipment/power, attack-jamming, attack-management-plane), start, end, affected_sites,
   root_cause, attack_stage, hard_case.

## Scenario knobs (train range / held-out harder range)
rain peak 20-120 / 120-180 mm/h; jamming J/N 3-15 / 0-3 dB; attacker dwell 10-60 min / 2-6 h;
sites affected 1-20 / 20-50; fibre cut 30 min-6 h / 12-48 h; battery start 40-100 / 15-40 %.

## Scenarios
U1 Deepavali payments wipe (management plane, KA-SAT pattern); U2 monsoon flood fibre cut +
rain fade vs jamming; U3 festival surge vs DoS; U4 Chepauk match temporary cells; U5 jammed
microwave forces failover into a trap path; U6 gateway power failure (looks like an attack,
is a fault). Plus H1-H4 healing and C0-C3 coordination scenarios from the report.
