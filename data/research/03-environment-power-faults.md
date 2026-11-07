# ORCA-NTN environment and infrastructure research report

## Summary

The data card already has useful telemetry fields for rain, weather, flood depth, battery state, and link fade. The main realism gains are to make them **spatially and temporally correlated**: monsoon rain should arrive in moving storm cells, flood depth should lag rainfall and depend on basin and drainage conditions, and grid and equipment faults should cluster during severe weather rather than occur independently.

A few limits affect how precisely this can be calibrated:

- ITU-R provides a global `R0.01` map, but I did not retrieve a Chennai grid-point value in this research pass. Treat the city value as **NOT FOUND here**; extract it from the map rather than substituting a seasonal maximum.
- The cited Turkcell repository confirms the dataset’s purpose, but the accessible repository description does not expose the raw TSV schema. A secondary paper lists six file names; it does not establish all raw column names, units, sampling intervals, or class prevalence. Those details are **NOT FOUND here** and should be checked against the actual download before matching column names.
- Public sources describe Chennai’s major flood events and flood vulnerable localities, but do not give a uniform street-level depth-versus-time series for every locality. Use event records and the official flood monitoring system for spatial calibration; mark synthetic flood-depth distributions as **ASSUMPTION** until fitted to those records.

Values in this report are classified as **physics/standard** (from ITU models), **observed** (reported for a specific event or source), **ASSUMPTION** (a simulation starting point), or **NOT FOUND**. None of the suggested simulation distributions should be read as official Chennai-wide operational statistics.

## 1. Chennai monsoon environment and flooding

Chennai’s northeast-monsoon season is not well represented by independent, stationary rain samples. The 2015 event featured several distinct spells, with heavy rainfall in November and a major late-November to early-December spell. A rapid assessment reported **49 cm at Tambaram** in the 24 hours ending 08:30 on 2 December 2015, compared with **34 cm at Chennai city**; the upper catchment also received more rain than the city. These are exceptional event totals, not typical hourly rain rates. [NITI Aayog’s 2015 flood report](https://www.niti.gov.in/sites/default/files/2023-02/Flood-Report.pdf), [Chennai floods rapid assessment](https://www.cag.org.in/sites/default/files/database/chennai-floods-rapid-assessment-report_1.pdf)

| Data-card field | Unit | Value or range to use | Suggested distribution and time pattern | Source / status |
|---|---:|---|---|---|
| `rain_rate_mm_h` | mm/h | Chennai `R0.01`: **NOT FOUND here**. The ITU-R P.837 maps provide a point value at Chennai coordinates. Separately, event totals in 2015 reached 490 mm/24 h at Tambaram. | Generate dry periods plus rain events. Use a zero-inflated event process and event-specific intensity curves; do not convert the 24-hour event total into a constant hourly rate. Spatially correlate nearby zones and allow upper-catchment rain to differ from city rain. | P.837-8 current recommendation and map listing: [ITU-R P.837](https://www.itu.int/rec/R-REC-P.837/en). 2015 event: [rapid assessment](https://www.cag.org.in/sites/default/files/database/chennai-floods-rapid-assessment-report_1.pdf). `R0.01` extraction required. |
| `rain_event_duration_min` | min | **NOT FOUND** as a Chennai NE-monsoon distribution. | **ASSUMPTION:** sample event durations with a right-skewed distribution, e.g. tens of minutes to several hours; include multi-day cyclone rain episodes as a separate event type. Fit to 1-minute automatic rain-gauge data if available. | No defensible citywide duration distribution found. Chennai flood system operates 117 automatic rain gauges: [CFM-DSS](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs). |
| `cyclone_rain_band_id` | categorical | **ASSUMPTION:** band identifiers or storm-relative distance/bearing, with coherent movement across zones. | Move rain bands across the synthetic map; use a shared storm track and time-varying intensity rather than a single citywide `cyclone_flag`. | The 2015 peer-reviewed event analysis links the rainfall to multiple synoptic systems: [MAUSAM 2015 deluge study](https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/5853). |
| `temp_C` | °C | No event-specific Oct–Dec range verified in this pass; **NOT FOUND**. | **ASSUMPTION:** use local IMD station observations or CFM-DSS AWS records, with diurnal cycles and weaker diurnal swings during persistent rain. | CFM-DSS AWS measures temperature: [official system description](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs). |
| `humidity_pct` | % | No Chennai monsoon distribution verified in this pass; **NOT FOUND**. | **ASSUMPTION:** correlate with rain and cloud cover, retain high humidity after rainfall, and vary by zone/time using observed AWS data. | CFM-DSS AWS measures relative humidity: [official system description](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs). |
| `wind_ms` / `gust_ms` | m/s | No specific Michaung station values retrieved here; **NOT FOUND**. | Use IMD/RSMC best-track and station observations when available. During cyclone scenarios, use a storm-relative wind field and gust process, not independent zone samples. | [IMD RSMC archive](https://rsmcnewdelhi.imd.gov.in/archive-report.php?internal_menu=MjY%3D&year=MjAyMw%3D%3D) lists the Michaung report. |
| `flood_depth_cm` | cm | No consistent observed time series by locality found here; **NOT FOUND**. | **ASSUMPTION:** nonnegative, zero-inflated depth; onset lags heavy rain and runoff, persistence continues after rain ends, and recession varies by drainage/basin. Generate correlated depth fields along watersheds and low-lying areas. | Chennai Flood Forecasting and Spatial Decision Support System identifies frequently flooded areas and operates hydrologic, channel, storm-drain, and inundation models: [CFM-DSS](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs). |
| `flood_locality_risk` | ordinal or probability | Higher-risk examples documented by the official Chennai basin system include **Velachery, Saidapet, Mambalam, Mudichur, Nungambakkam, and Meenambakkam**. | Assign locality risk from floodplain, watershed, drainage, and historic-event evidence. Avoid deterministic “always floods” labels; use event-conditioned probabilities. | [CFM-DSS](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs). |
| `flood_event_impacts_2015` | event label / locality | Reported affected locations include Tambaram, Mudichur, Kotturpuram, Pallavaram, Thiruneermalai, Urapakkam, Manapakkam, T. Nagar, and Guduvancheri, among others. | Use as a locality/event anchor, not as an occurrence frequency. | [PIB rescue update, 3 Dec 2015](https://www.pib.gov.in/newsite/PrintRelease.aspx?lang=2&reg=48&relid=132446); [NIDM Chennai flood report](https://nidm.gov.in/PDF/pubs/ChennailFlood_NIDM2021.pdf). |
| `flood_event_impacts_2023` | event label / locality | Michaung affected low-lying areas, with reporting around Velachery, Adambakkam, Madipakkam, Tambaram suburbs, and Adyar lowlands. Detailed station-level values are **NOT FOUND here**. | Use only as a historical event footprint until matched against official inundation layers or sensor records. | [IMD RSMC report archive](https://rsmcnewdelhi.imd.gov.in/archive-report.php?internal_menu=MjY%3D&year=MjAyMw%3D%3D); [NDRF Michaung operations](https://ndrf.mha.gov.in/en/operations/cyclone-michaung.html). |

The official Chennai flood system delineates 74 watersheds and incorporates rainfall, runoff, river/channel flow, reservoir operations, storm-drain, and 2D inundation models. Its monitoring network includes 117 automatic rain gauges, 30 automatic weather stations, 185 water-level recorders, and 58 gate sensors. These are good candidate sources for calibrating the `weather` table if their observations can be accessed. [CFM-DSS](https://chennaifloodmonitor.tn.gov.in/Master/AboutUs)

## 2. Rain and atmospheric attenuation

For terrestrial microwave links, ITU-R P.530-19 covers line-of-sight link design and rain attenuation at higher frequencies. For Earth-space links, use P.618-14; it depends on precipitation characteristics including `R0.01`, and models rain and other atmospheric effects for satellite paths. P.838-3 supplies the specific attenuation law:

\[
\gamma_R = k R^\alpha
\]

where `rain_rate_mm_h` is \(R\), and polarization- and frequency-dependent `k` and `alpha` produce specific attenuation in dB/km. Apply the path reduction methods in P.530 or P.618 to obtain link fade; do not treat \(\gamma_R\) as the total path fade. [ITU-R P.838-3](https://www.itu.int/rec/r-rec-p.838-3-200503-i/en), [ITU-R P.530-19](https://www.itu.int/rec/R-REC-P.530-19-202509-I/en), [ITU-R P.618-14](https://www.itu.int/rec/R-REC-P.618/en)

The following are representative rounded **horizontal-polarization** P.838-3 values. For production, compute coefficients from the recommendation’s equations/table for the exact frequency and polarization in each site record.

| Data-card field | Unit | Value or range | Suggested distribution and time pattern | Source / status |
|---|---:|---|---|---|
| `rain_specific_attenuation_k_h` | coefficient | At 7, 12, 20, 30, 38 GHz: approximately **0.0019, 0.0188, 0.0916, 0.240, 0.443** | Deterministic function of frequency and polarization; no stochastic sampling. | [ITU-R P.838-3](https://www.itu.int/rec/r-rec-p.838-3-200503-i/en). Rounded representative values. |
| `rain_specific_attenuation_alpha_h` | dimensionless | At 7, 12, 20, 30, 38 GHz: approximately **1.40, 1.22, 1.06, 0.95, 0.87** | Deterministic function of frequency and polarization. | [ITU-R P.838-3](https://www.itu.int/rec/r-rec-p.838-3-200503-i/en). Rounded representative values. |
| `rain_specific_attenuation_k_v` / `rain_specific_attenuation_alpha_v` | coefficient / dimensionless | Values differ from horizontal polarization; calculate explicitly for vertical or circular polarization. | Deterministic from frequency and polarization. | [ITU-R P.838-3](https://www.itu.int/rec/r-rec-p.838-3-200503-i/en). |
| `expected_fade_dB` | dB | Model output; no fixed Chennai range. | Calculate from rain rate, frequency, polarization, elevation/path geometry and the relevant P.530/P.618 method. Use the same 10-second rain/link time base, with rain aggregation consistent with model assumptions. | [P.530-19](https://www.itu.int/rec/R-REC-P.530-19-202509-I/en); [P.618-14](https://www.itu.int/rec/R-REC-P.618/en). |
| `wet_antenna_loss_dB` | dB | **NOT FOUND** for the proposed hardware and installation. | **ASSUMPTION:** a separate transient state triggered by rain/water film, with persistence and drying after rain. Keep it separate from propagation-path rain attenuation to avoid conflating the mechanisms. Calibrate only if antenna-specific measurements are available. | No hardware-specific source found. |
| `sun_outage_flag` | boolean | GEO solar conjunction occurs around the equinox seasons, with precise dates depending on satellite longitude and antenna geometry. Exact Chennai dates are **NOT FOUND** without satellite longitude and dish parameters. | Compute from station coordinates, GEO longitude, antenna beamwidth, and a solar ephemeris; model short daily events across a seasonal window. Do not set a generic outage at all sites or all satellite longitudes. | ITU Earth-space propagation methods: [P.618-14](https://www.itu.int/rec/R-REC-P.618/en). Exact operational window requires the actual GEO orbital longitude/antenna geometry. |

The frequency values above extend the data card’s microwave range. Use `mw_freq_GHz` and `polarisation` to determine coefficients per link. For satellite links, Ku around 12 GHz and Ka around 20/30 GHz should use the same coefficient logic, but the path geometry differs: Earth-space slant path and elevation angle matter.

## 3. Power systems and power-related faults

TRAI and telecom-sector sources describe Indian tower sites using batteries and standby diesel generators, with solar/hybrid systems also deployed. The data card can model these as explicit site configurations. National or India-wide power availability figures should not be treated as Chennai site-level outage distributions; those require local distribution-utility data. A reliable Chennai-specific `SAIDI`/`SAIFI` time series was **NOT FOUND** in this pass.

| Data-card field | Unit | Value or range | Suggested distribution and time pattern | Source / status |
|---|---:|---|---|---|
| `grid_outage_duration_min` | min | Chennai urban site-level distribution: **NOT FOUND**. | **ASSUMPTION:** model outages as clustered, site/feeder-correlated events; increase outage probability during severe floods and wind events. Use actual utility/site logs to fit. | Local site-level outage series not retrieved. |
| `grid_availability_pct` | % | **NOT FOUND** for the modeled sites. | Derive from observed `grid_on` records, not a generic national average. | CEA utility reliability metrics/local DISCOM data required. |
| `battery_type` | categorical | `VRLA` and `lithium_ion` are valid telecom battery classes; exact mix at modeled sites is **NOT FOUND**. | Static site attribute, with different usable capacity and aging behavior by chemistry. | DoT TEC publishes telecom battery guidance and standards: [TEC guidelines](https://tec.dssolution.in/guidelines); [DoT Annual Report 2024–25](https://www.dot.gov.in/static/uploads/2025/07/8df49d5b579439471bb8e506906d913a.pdf). |
| `battery_autonomy_h` | h | Site-specific value **NOT FOUND**. For modeling, choose capacity from load and a declared backup target, rather than inventing a universal Indian value. | **ASSUMPTION:** calculate nominal autonomy as usable `battery_kWh / typical_load_kW`; reduce usable energy with battery aging, temperature, and discharge limit. | GSMA India tower energy paper describes battery bridging the grid-to-generator transition and availability design: [GSMA report](https://www.gsma.com/membership/wp-content/uploads/2013/01/true-cost-providing-energy-telecom-towers-india.pdf). |
| `battery_soc_pct` | % | 0–100 by definition; usable operating thresholds depend on chemistry and configuration. | Integrate charge/discharge from `load_kW`, grid/genset/solar source, efficiency, and capacity; do not sample SOC independently each minute. | Physics-based bookkeeping; chemistry standards in [TEC guidelines](https://tec.dssolution.in/guidelines). |
| `battery_temp_C` | °C | Site-specific thermal distribution **NOT FOUND**. | **ASSUMPTION:** correlate with ambient `temp_C`, cabinet ventilation, and battery charge/discharge; model thermal inertia. | No Chennai tower battery temperature dataset found. |
| `battery_capacity_derate_pct` | % | **NOT FOUND** for the selected battery models and temperature range. | Use manufacturer curves once battery model is chosen; otherwise label the derating function **ASSUMPTION** and keep it modest/explicit. | Model-specific manufacturer data required. |
| `genset_start_delay_s` | s | **NOT FOUND** for proposed hardware. | **ASSUMPTION:** site-specific startup delay; generate rare start failures as separate equipment faults. | No equipment model specified. |
| `genset_fuel_remaining_pct` | % | **NOT FOUND**. | Decrease while running; refuel access can be delayed during flood events. | **ASSUMPTION** pending chosen genset/fuel capacity and logistics model. |
| `solar_generation_kW` | kW | Site-specific installed capacity **NOT FOUND**. | **ASSUMPTION:** derive from installed PV capacity, hour-of-day solar profile, and cloud/rain attenuation; near-zero output at night and reduced output during heavy cloud/rain. | DoT lists planning guidance for solar PV telecom systems: [TEC guidelines](https://tec.dssolution.in/guidelines). |
| `site_load_kW` | kW | **NOT FOUND** by site type in Chennai. A published India BESS estimate uses an assumed **3.5 kW/site** and 8 h outage, but explicitly depends on assumptions and site configuration. | Use separate low/medium/high load profiles by site type, marked **ASSUMPTION** until measured. Add a weather-dependent cooling component where the site uses air conditioning. | [India telecom BESS report](https://assets.ctfassets.net/6sce2o5alp4f/3GRp1uB9ruehQDsi0tU6WJ/19c2b89d3215c8d7afc0cbd0af5302a0/wp1.pdf); [GSMA India energy report](https://www.gsma.com/membership/wp-content/uploads/2013/01/true-cost-providing-energy-telecom-towers-india.pdf). |

Use explicit energy-source transitions (`grid → battery → genset`, with solar as a site option) and separate component failure flags such as `battery_failed`, `genset_failed`, and `fuel_shortage`. Rain/flood events can affect access, fuel delivery, or low-mounted power equipment, but those correlations should be labelled **ASSUMPTION** until supported by site records.

## 4. Equipment, backhaul, and maintenance faults

The cited public material does not establish Chennai-specific radio link failure probabilities, fibre cut rates, repair times, microwave hardware MTBF, or satellite gateway fault rates. These should not be populated as if they were official local statistics.

| Data-card field | Unit | Value or range | Suggested distribution and time pattern | Source / status |
|---|---:|---|---|---|
| `rlf_rate_per_link_day` | failures/link/day | Chennai value **NOT FOUND**. | Calibrate to the real Turkcell dataset only after verifying its labels and sampling. Keep weather-induced degradation and hard RLF events distinct. | Turkcell repository describes anonymized regional weather and radio-link performance/RLF data: [GitHub](https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021). |
| `rlf_cause` | categorical | Examples for simulation: rain fade, power loss, equipment, path obstruction, interference. Chennai-specific proportions are **NOT FOUND**. | Use labeled scenario causes; do not infer ground truth from telemetry alone. | **ASSUMPTION** for scenario taxonomy. |
| `fibre_cut_rate_per_km_year` | cuts/(km·year) | **NOT FOUND** for Chennai. | **ASSUMPTION:** use rare spatially clustered cuts; increase hazard near flood-prone routes only if routes are mapped and the relationship is declared as a scenario assumption. | No local cut-rate source found. |
| `fibre_repair_duration_h` | h | Chennai distribution **NOT FOUND**. Existing data-card scenario range is **30 min–6 h** for training and **12–48 h** for held-out harder cases; these are scenario knobs, not sourced statistics. | Right-skewed repair durations; access constraints can lengthen flood-event repairs. Clearly label the range **ASSUMPTION**. | Values from the supplied data card, not an external operational statistic. |
| `submarine_cable_fault_count` | faults/event or faults/year | Chennai-specific rate **NOT FOUND**. | Model as a shared upstream connectivity impairment only if a named cable landing and fault scenario are specified; do not present it as a local fibre cut. | No local frequency/repair series retrieved. |
| `microwave_radio_mtbf_h` | h | **NOT FOUND** for proposed hardware. | Use vendor-specific MTBF once radios are selected; otherwise represent rare `microwave_hardware_fault` as a scenario event, not a purported empirical rate. | No hardware model or vendor data. |
| `satellite_modem_fault_rate` | faults/site/year | **NOT FOUND** for proposed modems/gateway. | **ASSUMPTION:** rare equipment-fault process separate from weather fades and sun outage. | No modem/gateway model or field data. |
| `gateway_power_fault` | boolean/event | **NOT FOUND** for real gateway availability. | Scenario-based correlated outage affecting multiple dependent sites; distinguish grid failure, battery depletion, genset failure, and equipment fault. | **ASSUMPTION** consistent with data-card scenario U6. |
| `maintenance_window_start` / `maintenance_window_end` | local datetime | Operator schedule **NOT FOUND**. | **ASSUMPTION:** configure site-specific planned windows and lower their event rate during severe weather; log planned maintenance separately from unplanned faults. | No operator maintenance schedule found. |
| `repair_access_delay_h` | h | **NOT FOUND**. | **ASSUMPTION:** event-dependent delay, increasing for flood-affected access routes. | Requires route/accessibility data. |

Avoid using the data-card’s fibre repair scenario ranges or synthetic attack/fault rates as a statement of observed Indian telecom performance. They are useful controlled knobs, but should be explicitly tagged as scenario assumptions.

## 5. Turkcell / ITU radio-link-failure data

The Turkcell repository describes an anonymized dataset joining regional weather information to historical radio-link performance and RLF outcomes. The public project is the right calibration candidate, but schema details could not be verified from its accessible repository description in this pass. A secondary paper lists the following files inside the dataset archive:

| File | Description in secondary source | Schema details verified here |
|---|---|---|
| `distances.tsv` | Pair-wise distances | Column names/units: **NOT FOUND** |
| `met-forecast.tsv` | Five-day meteorology forecasts | Column names/units/sampling: **NOT FOUND** |
| `met-real.tsv` | Historical meteorological realizations | Column names/units/sampling: **NOT FOUND** |
| `met-stations.tsv` | Meteorological station information | Column names/units: **NOT FOUND** |
| `rl-kpis.tsv` | Radio-link KPIs and configuration parameters | Column names/units/sampling/label encoding: **NOT FOUND** |
| `rl-sites.tsv` | Radio-link site information | Column names/units: **NOT FOUND** |

The repository itself says it includes regional historical weather forecasts, realized weather and radio-link performance for a given frequency band, and that the data is anonymized. [Turkcell repository](https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021) The file inventory above is reported by a secondary implementation paper, not by the raw data dictionary. [Sivakumar et al., ITU Journal on Future and Evolving Technologies](https://doi.org/10.52953/lzlj8762)

Therefore, the following requested metadata remain **NOT FOUND**:

- Exact table/column names and capitalization.
- Units and categorical encodings for every column.
- Sampling interval and time-zone conventions.
- Definition/window for an RLF label.
- Positive-class prevalence/class imbalance.
- Data split boundaries and potential link/site grouping.

Before matching ORCA-NTN columns to Turkcell, inspect the actual archive and preserve its original names in a separate compatibility layer. The 10-second ORCA telemetry is much higher frequency than a five-day weather forecast problem may require; do not assume their sampling grids are interchangeable.

## 6. Synthetic-data realism checks

The checks below are validation methods, not parameters to sample. Evaluate environmental and infrastructure realism separately from traffic and attacks, which are outside this report’s scope.

| Validation field | Unit | Suggested check | Time pattern / split design | Source / status |
|---|---:|---|---|---|
| `validation_univariate_distance` | statistic | Compare observed and synthetic marginals with empirical CDFs, quantile error, Wasserstein distance, and KS tests where sample assumptions permit. | Compare by season, site type, rain regime, and event class; do not pool normal and cyclone periods. | Standard statistical validation; choose thresholds based on use case. |
| `validation_temporal_dependence` | statistic | Compare autocorrelation, rain-event duration/intensity curves, flood lag/recession, outage run lengths, battery SOC trajectories, and cross-correlation between rain/flood/power/link degradation. | Use event-held-out and time-held-out splits to test persistence and generalization. | Recommended methodology; thresholds are **ASSUMPTION**. |
| `validation_spatial_dependence` | statistic | Compare semivariograms or distance-conditioned correlations for rainfall, flood depth, and shared outages. | Hold out zones or watersheds, not randomly selected rows from the same event. | Recommended methodology; thresholds are **ASSUMPTION**. |
| `train_on_synthetic_test_on_real` | metric | Train on synthetic data and test on real held-out records; compare with real-train/real-test baseline. Report AUROC plus PR-AUC, recall at fixed false-alarm rate, and calibration for rare faults/RLFs. | Split by time, site/link, and storm/event to avoid leakage. | Use real target data only where licensing and privacy permit. |
| `domain_gap_score` | statistic | Train a classifier to distinguish synthetic from real rows; high held-out discrimination indicates a feature-level domain gap. Inspect which features drive it. | Report by weather regime and fault class; tune simulator, then re-evaluate on untouched real data. | Methodological recommendation; no domain-gap threshold is universal. |
| `synthetic_privacy_check` | qualitative / statistic | If real traces inform calibration, assess whether synthetic rows reproduce or reveal individual real records; avoid copying raw records as “synthetic.” | Keep calibration and evaluation data disjoint. | Recommended practice. |

Because the Turkcell corpus is described as anonymized, it can help calibrate radio-link relationships, but it is not evidence that Chennai climate, power, or flood distributions match. Use Chennai-local weather and flood sources for those components, and state any cross-domain transfer explicitly.

## New data-card fields

Recommended additions to the draft data card:

| Field | Why add it |
|---|---|
| `rain_event_id`, `rain_event_type`, `storm_track_id`, `storm_relative_distance_km` | Preserve coherent storm/rain-band structure. |
| `rain_rate_1min_mm_h`, `rain_accum_1h_mm`, `rain_accum_24h_mm` | Separate instantaneous rate from accumulation and enable comparison with IMD reports. |
| `flood_depth_source`, `watershed_id`, `drainage_risk_class`, `flood_onset_lag_min`, `flood_recession_rate_cm_h` | Make flood generation interpretable and calibratable. |
| `wind_direction_deg`, `wind_gust_ms`, `solar_irradiance_W_m2` | Needed for cyclone impacts and solar generation; weather station network measures wind direction and irradiance. |
| `rain_specific_attenuation_dB_km`, `rain_attenuation_model`, `wet_antenna_loss_dB` | Separate propagation-model output and antenna wetting from measured link degradation. |
| `battery_type`, `battery_capacity_kWh`, `battery_health_pct`, `battery_usable_soc_floor_pct`, `battery_capacity_derate_pct` | Represent chemistry, aging, and usable capacity explicitly. |
| `grid_feeder_id`, `outage_event_id`, `genset_failed`, `fuel_remaining_pct`, `solar_generation_kW`, `power_source` | Support correlated grid outages and realistic backup transitions. |
| `fault_component`, `fault_start`, `fault_end`, `repair_access_delay_h`, `maintenance_flag` | Distinguish equipment failures, repair delays, and planned maintenance. |
| `rlf_label_definition`, `rlf_window_s`, `rlf_event_id`, `rlf_class_weight` | Document label semantics and class imbalance once the Turkcell schema is inspected. |
| `source_class` (`physics`, `observed`, `calibrated`, `assumed`) | Make provenance visible per field/parameter, aligning with the data card’s existing source categories. |

## Open questions

1. Can the Turkcell archive be downloaded and inspected so exact TSV schemas, units, sampling, label definitions, and class prevalence can be recorded?
2. Can the current P.837-8 digital map be sampled at Chennai and the proposed site coordinates to record official `R0.01` values?
3. Can the synthetic site list be linked to a watershed, elevation, flood-prone area, and likely distribution feeder?
4. Are Chennai IMD/CFM-DSS automatic rain, weather, and water-level observations accessible for calibration or only public dashboard viewing?
5. Which GEO satellite longitude, elevation angle, and terminal antenna beamwidth should define `sun_outage_flag`?
6. Which microwave radios, satellite modems, batteries, gensets, and gateway hardware are assumed? Vendor datasheets are required for defensible MTBF, power, and temperature derating.
7. Can local DISCOM reliability reports or tower operator logs provide Chennai-area outage counts, duration distributions, fibre repair times, and maintenance windows?

I did not modify any files.