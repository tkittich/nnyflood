# Independent Audit & Red-Team Technical Report: nnyflood
**Date**: 2026-10-17  
**Auditor**: Independent Senior Hydraulic Engineer & Lead Data Science Auditor (Red-Team Reviewer)  
**Target System**: `nnyflood` (Pillars 1–3: Goals 1–7)  
**Status**: Completed · 10 Findings Cataloged (4 High, 4 Medium, 2 Low)

---

## 1. Executive Summary

### 1.1 Scope & Mission
This audit conducted an exhaustive, evidence-based red-team technical review of the `nnyflood` hydrological codebase, analytical pipelines, machine learning architectures, and published technical reports. The audit targeted mathematical correctness, physical hydrodynamic validity, data leakage, empirical alignment with primary telemetry, and compliance with the project's legal/PDPA directives.

### 1.2 Overall System Assessment
- **Overall Scientific & Engineering Reliability**: **Medium-High**  
  The core hydrological foundational work (cross-sectional bathymetry extraction, multi-reservoir baseline statistics, and unified verification) is solid, rigorously tested (10/10 test suites passing), and reproducible. However, advanced coupling models (Muskingum-Cunge 1D routing, coastal ML feature extraction, and counterfactual floodway simulation) suffer from numerical stability violations, silent data loading bugs, and idealized boundary assumptions that must be triaged prior to policy citation.

### 1.3 Key Validated Strengths
1. **Empirical Survey Geometry Integration**: Utilization of Eastern Region Irrigation Hydrology Center surveyed river cross-sections (61–68 points per station) provides authentic bed levels (thalweg $-2.396\text{ m}$ MSL at Ny.7; $+2.233\text{ m}$ MSL at Ny.1B), successfully debunking arbitrary digital elevation model artifacts.
2. **Defamation & PDPA Governance**: Strict adherence to `docs/LEGAL_REVIEW.md` is maintained across all technical documentation; critiques focus entirely on hydraulic infrastructure, rule curves, and systemic operating constraints without attributing personal negligence to individual public servants.
3. **Rigorous Test & Verification Tooling**: The multi-stage verification runner (`python tools/verify_all.py`) and pre-commit checks maintain zero raw data hash mismatches (SHA-256) and zero catalog drift across 199 files.

### 1.4 Critical Vulnerabilities
1. **Muskingum-Cunge Numerical Stability Breakdown**: Reach routing across 18.3 km in a single spatial step ($\Delta x = 18,300\text{ m}$) causes the Courant stability condition $2KX \le \Delta t$ to fail, generating negative coefficients ($c_1 < 0$) and numerical dip.
2. **Silent Zero-Feature Parsing Bug in Coastal ML**: In `analysis/goal6_l3_coastal_model.py`, a dictionary type check against nested JSON results in `rain_data` remaining empty, causing the rainfall feature `r24` to evaluate to `0.0` for 100% of samples.
3. **Synthetic Hydrograph & Arbitrary Attenuation in CP2 Simulation**: The 2011 mega-flood counterfactual in `analysis/goal7_counterfactual_simulation.py` is simulated via a synthetic sine wave and an arbitrary calibration divisor (`1100.0`), while coastal tidal lockouts are simplified to a minor scalar multiplier ($\ge 84\%$).

---

## 2. Findings Matrix & Triage Summary

| ID | Severity | Component / Target File | Root Cause Summary | Impact | Triage Priority | Recommended Fix |
|---|---|---|---|---|---|---|
| **F-01** | **High** | `analysis/hydraulic_1d_routing.py:111-131, 180-185` | Single-step spatial routing ($\Delta x = 18.3\text{ km}$, $\Delta t = 900\text{ s}$) yields negative coefficient $c_1 \approx -0.37$ to $-0.77$. | Numerical instability, artificial steepening, and distorted wave attenuation. | **P1 (Immediate)** | Subdivide reach into $N \approx 12$ sub-reaches ($\Delta x_{\text{sub}} \approx 1.5\text{ km}$). |
| **F-02** | **High** | `analysis/hydraulic_1d_routing_summary.json:32-33`, `HANDOFF.md:39` | 43 km full-basin travel time ($7.37\text{ h}$) conflated with 18.3 km reach ($3.14\text{ h}$); telemetry peak Q has 24.25 h lag from isolated spike. | Technical confusion across documentation; 106.9 cm stage RMSE. | **P1 (Immediate)** | Clarify reach vs full-basin metrics; smooth telemetry Q using stage rating curves. |
| **F-03** | **High** | `analysis/goal6_l3_coastal_model.py:81-88` | Dictionary type-check bug on nested JSON (`nasa_power_2026.json`) leaves `rain_data` empty. | Feature `r24` is 100% zeros; model trained completely without rainfall. | **P1 (Immediate)** | Unnest `raw_r["กรุงเทพกลาง"]["daily"]` to populate `rain_data`. |
| **F-04** | **Medium** | `analysis/goal6_l3_coastal_model.py:90-98, 160-164` | Tidal phase resets modulo 24 h at midnight; SWAN wave height is loaded as a constant scalar ($0.8\text{ m}$). | Artificial midnight phase jumps; wave height provides zero predictive variance. | **P2 (Near-Term)** | Compute phase from continuous elapsed hours ($t - t_0$); ingest dynamic hourly SWAN series. |
| **F-05** | **Medium** | `analysis/goal6_l3_coastal_model.py:8, 101-102` | Scope discrepancy: Script documentation claims 2020–2026 multi-year training, but code hardcodes `start_dt = 2026-07-01` (47 days). | Overstated model generality in documentation. | **P2 (Near-Term)** | Clarify scope as single-season wet season baseline, or load multi-year archives. |
| **F-06** | **Medium** | `analysis/compound_flood_risk.py:30-43` | Purely additive backwater formulation: $H_{\text{C12}} = H_{\text{tide}} + \Delta h_{\text{wave}} + c_1(Q/1000)^{1.28}$ ignores depth-friction coupling. | Overestimates upstream head loss during high tide backwater conditions. | **P2 (Near-Term)** | Couple friction loss to water depth ($y = H_{\text{stage}} - z_{\text{bed}}$). |
| **F-07** | **Low** | `analysis/compound_flood_risk.py:100-106` | Benchmark scenario 3 stage ($2.85\text{ m}$ MSL) exceeds floodwall ($2.80\text{ m}$) but status string labels it "Orange Warning". | Textual contradiction with internal risk threshold table ($>2.70\text{ m}$ = Critical). | **P3 (Maintenance)** | Update status string to "ระดับวิกฤตล้นคันกั้นน้ำ (สีแดง)". |
| **F-08** | **High** | `analysis/goal7_counterfactual_simulation.py:75-77, 96-105` | 2011 inflow is a synthetic sine curve; Ayutthaya stage reduction ($0.53\text{ m}$) uses an arbitrary divisor ($1100.0$). | Unverified peak shaving claims (4,394.5 MCM, 40.0% excess volume absorbed). | **P1 (Immediate)** | Route actual 2011 C.13/S.26 hydrograph; calibrate stage reduction against C.35 rating curve. |
| **F-09** | **Low** | `analysis/goal7_counterfactual_simulation.py:199, 211` | Matplotlib plot titles hardcode $3,695$ and $756\text{ MCM}$, contradicting simulated outputs ($4,394.5$ and $215.8\text{ MCM}$). | Discrepancy between chart titles and canonical JSON metrics. | **P3 (Maintenance)** | Make chart titles dynamic using f-strings referencing simulation dictionaries. |
| **F-10** | **Medium** | `analysis/goal6_pasak_24y_baseline.py:25-27, 109-114` | Storage exceeding `MAX_CAP` ($1,036.16\text{ MCM}$) in 2010 ($1,177.22\text{ MCM}$ / 135.1%) risks being misread as dam overtopping. | Potential public misunderstanding of structural safety. | **P2 (Near-Term)** | Clarify distinct zones: Active conservation, designed surcharge, and freeboard buffer. |

---

## 3. Detailed Technical Audit Findings

### [F-01] Muskingum-Cunge Numerical Stability Breakdown via Single-Reach Routing
- **Location**: `analysis/hydraulic_1d_routing.py:111-131`, `analysis/hydraulic_1d_routing.py:180-185`
- **Empirical Evidence**:
  In `analysis/hydraulic_1d_routing.py`:
  ```python
  dt_sec = 15.0 * 60.0  # 15 min = 900 s
  dx_m = 18300.0        # 18.3 km
  ```
  Evaluating the internal equations across the observed discharge regime:
  ```python
  # Q = 50 m3/s:  c_wave = 0.66 m/s, K = 27,576 s, X = 0.450 -> c1 = -0.7658, c2 = 0.8234, c3 = 0.9424
  # Q = 300 m3/s: c_wave = 1.36 m/s, K = 13,467 s, X = 0.377 -> c1 = -0.5232, c2 = 0.6250, c3 = 0.8982
  # Q = 600 m3/s: c_wave = 1.79 m/s, K = 10,206 s, X = 0.313 -> c1 = -0.3686, c2 = 0.4893, c3 = 0.8793
  ```
- **Hydraulic & Data Science Critique**:
  In hydraulic engineering (Cunge 1969; Ponce 1989), Muskingum-Cunge routing accurately mimics diffusion wave propagation only when the space-time grid satisfies:
  $$C = \frac{c \cdot \Delta t}{\Delta x} \approx 1 \quad \text{and} \quad 2 K X \le \Delta t \le 2 K (1 - X)$$
  With $\Delta x = 18,300\text{ m}$ and $\Delta t = 900\text{ s}$, $2KX$ equals $6,388\text{ s}$ at $600\text{ m}^3\text{/s}$, which is over 7 times larger than $\Delta t$ ($900\text{ s}$). This forces $c_1$ into negative territory ($c_1 = -0.3686$). Negative $c_1$ causes non-physical negative initial outflow responses ("dip") and severe artificial steepening/distortion of the routed flood wave.
- **Proposed Solution**:
  Subdivide the 18.3 km reach into $N$ sub-reaches:
  $$\Delta x_{\text{sub}} \approx c \cdot \Delta t \approx 1.62\text{ m/s} \times 900\text{ s} \approx 1,458\text{ m} \implies N = 12$$
  Loop sequentially through the 12 sub-reaches so that $c_1, c_2, c_3 \ge 0$.

---

### [F-02] Conflation of Reach Lengths and Telemetry Noise in Flood Travel Time
- **Location**: `analysis/hydraulic_1d_routing_summary.json:31-38`, `HANDOFF.md:39`, `docs/REVIEW_PROMPT_EN.md:16`
- **Empirical Evidence**:
  1. `analysis/hydraulic_1d_routing_summary.json`:
     ```json
     "routing_performance": {
       "travel_time_hours_sim": 2.0,
       "travel_time_hours_obs": 24.25,
       "rmse_discharge_cms": 126.13,
       "rmse_stage_cm": 106.9,
       "q_peak_sim_cms": 578.7,
       "q_peak_obs_cms": 648.3
     }
     ```
  2. `HANDOFF.md:39`:
     > "ความเร็วคลื่นน้ำหลาก 1.62 ม./วินาที (ใช้เวลาเคลื่อนตัว $7.37 \pm 0.8$ ชม.) สอดคล้องกับฮิสโตแกรมความล่าช้า 6–8 ชม."
  3. Raw telemetry data inspection (`data/20_multistation_levels/st61.csv` vs `st62.csv`):
     - `st61` (Ny.1B): Peak $Q = 675.3\text{ m}^3\text{/s}$ at `2026-09-26 18:30:00`; Stage peak at `2026-09-27 01:00:00` ($11.00\text{ m}$ MSL).
     - `st62` (Ny.7): Stage peak at `2026-09-27 10:00:00` ($7.68\text{ m}$ MSL); isolated $Q$ spike of $648.3\text{ m}^3\text{/s}$ recorded at `2026-09-27 18:45:00` while stage was only $7.57\text{ m}$ MSL.
- **Hydraulic & Data Science Critique**:
  A dimensional conflation exists between three separate metrics:
  - Basin scale ($43\text{ km}$): $43,000\text{ m} / (1.62\text{ m/s} \times 3600) = 7.37\text{ hours}$.
  - Reach scale ($18.3\text{ km}$): $18,300\text{ m} / (1.62\text{ m/s} \times 3600) = 3.14\text{ hours}$.
  - Observed telemetry stage peak lag: `2026-09-27 01:00` to `2026-09-27 10:00` = $9.0 - 9.5\text{ hours}$.
  The script computed observed lag by finding `argmax(q_obs_ny7)`, which caught an isolated telemetry glitch at 18:45 on September 27, resulting in a spurious 24.25-hour lag. Concurrently, the text in `HANDOFF.md` attributed the full-basin $7.37\text{ h}$ travel time to the 18.3 km reach.
- **Proposed Solution**:
  1. Update `HANDOFF.md` and documentation to explicitly state: full basin (43 km) travel time is $\approx 7.4\text{ h}$; reach travel time (18.3 km) is $\approx 3.1\text{ h}$.
  2. In `hydraulic_1d_routing.py`, calculate travel time using smoothed stage hydrographs or discharge derived via monotonic rating curves, rather than raw unverified $Q$ spikes.

---

### [F-03] Silent Zero-Feature Parsing Bug in Coastal Machine Learning Model
- **Location**: `analysis/goal6_l3_coastal_model.py:81-88`
- **Empirical Evidence**:
  Lines 81–88:
  ```python
  rain_data = {}
  p_rain = RAW_DIR / "nasa_power_2026.json"
  if p_rain.exists():
      raw_r = json.loads(p_rain.read_text(encoding="utf-8"))
      for k, v in raw_r.items():
          if isinstance(v, (int, float)):
              rain_data[k] = float(v)
  ```
  Inspecting `nasa_power_2026.json`:
  ```json
  {"กรุงเทพกลาง": {"daily": {"2026-01-01": 0.0, ...}}, "ปากน้ำ": {"daily": {...}}}
  ```
  Executing verification in terminal:
  ```python
  >>> len(rain_data)
  0
  ```
  In lines 147–150:
  ```python
  d_curr = t_curr.split()[0].replace("-", "")
  r24 = rain_data.get(d_curr, 0.0)  # Always evaluates to 0.0
  ```
- **Hydraulic & Data Science Critique**:
  The dictionary iteration checks `isinstance(v, (int, float))` at the root level, where all values are nested dicts. `rain_data` is left empty, causing the rainfall feature `r24` to be identical to 0.0 across all 1,392 hourly rows. Both the Baseline and Coastal-Coupled models were trained without precipitation input.
- **Proposed Solution**:
  Extract daily data from the nested station dictionary:
  ```python
  rain_data = {}
  if p_rain.exists():
      raw_r = json.loads(p_rain.read_text(encoding="utf-8"))
      daily_dict = raw_r.get("กรุงเทพกลาง", {}).get("daily", {})
      rain_data = {k.replace("-", ""): float(v) for k, v in daily_dict.items()}
  ```

---

### [F-04] Astronomical Tide Phase Reset Modulo 24 Hours & Static Wave Height
- **Location**: `analysis/goal6_l3_coastal_model.py:90-98`, `analysis/goal6_l3_coastal_model.py:160-164`
- **Empirical Evidence**:
  Lines 160–162:
  ```python
  hour_float = dt.datetime.fromisoformat(t_curr).hour
  tide_phase_sin = math.sin(2.0 * math.pi * hour_float / 12.42)
  tide_phase_cos = math.cos(2.0 * math.pi * hour_float / 12.42)
  ```
  At 23:00 on Day 1:
  $$\theta = 2\pi \times \frac{23}{12.42} \approx 3.703\pi \equiv 1.703\pi \implies \sin(\theta) \approx -0.803$$
  At 00:00 on Day 2:
  $$\theta = 2\pi \times \frac{0}{12.42} = 0 \implies \sin(\theta) = 0.000$$
  Lines 90–98:
  `swan_hs = 0.8` is hardcoded as a scalar constant when reading `gulf_wave_summary.json` if hourly profiles are absent.
- **Hydraulic & Data Science Critique**:
  The semidiurnal lunar tide ($M_2$) has a period of 12.4206 hours. Lunar tides do not align with the 24-hour solar day and advance by ~50 minutes per day. By computing phase using the diurnal solar hour (`dt.hour`), the phase wraps modulo 24, introducing an artificial 11.58-hour jump across midnight. Furthermore, including a constant scalar `swan_hs` (0.8 m) provides zero variance for tree splitting in GBDT and is collinear with the intercept in linear regression.
- **Proposed Solution**:
  1. Base tidal phase on continuous elapsed hours from an initial reference timestamp:
     ```python
     elapsed_hours = (dt.datetime.fromisoformat(t_curr) - start_dt).total_seconds() / 3600.0
     tide_phase_sin = math.sin(2.0 * math.pi * elapsed_hours / 12.4206)
     ```
  2. Ingest time-varying SWAN significant wave height time series, or drop `swan_hs` if only static offshore means are available.

---

### [F-05] Scope Discrepancy: Missing Multi-Year Training Partition
- **Location**: `analysis/goal6_l3_coastal_model.py:8`, `analysis/goal6_l3_coastal_model.py:101-102`, `analysis/goal6/l3_coastal_summary.json:19-20`
- **Empirical Evidence**:
  The script header and prompt state: "Train: 2020–2026 wet seasons up to Sep 20; Test: Sep 20 – Oct 9, 2026".
  However, line 101 executes:
  ```python
  start_dt = dt.datetime(2026, 7, 1, 0, 0)
  ```
  `l3_coastal_summary.json` records `n_train = 1130` (47 days). Data from 2020–2025 is never loaded.
- **Hydraulic & Data Science Critique**:
  Evaluating machine learning models on a single seasonal flood wave without multi-year cross-validation risks overfitting to the idiosyncratic hydrometeorology of late 2026.
- **Proposed Solution**:
  Update script docstrings to explicitly describe the scope as a single-season pilot baseline (2026 wet season), or ingest the multi-year raw files present in `data/22_goal6_network/`.

---

### [F-06] Decoupled Linear Superposition in Compound Flood Risk Matrix
- **Location**: `analysis/compound_flood_risk.py:30-43`
- **Empirical Evidence**:
  ```python
  def calculate_c12_stage(q_bangsai: float, tide_msl: float, wave_setup_m: float = 0.08) -> float:
      c1 = 0.132
      head_loss = c1 * ((q_bangsai / 1000.0) ** 1.28)
      stage = tide_msl + wave_setup_m + head_loss
      return round(float(stage), 2)
  ```
  Note: Docstring states $(Q/1000)^{1.25}$ while code implements $(Q/1000)^{1.28}$.
- **Hydraulic & Data Science Critique**:
  In open-channel backwater hydraulics:
  $$\frac{dy}{dx} = \frac{S_0 - S_f}{1 - Fr^2}, \quad S_f = \frac{n^2 Q^2}{A^2 R^{4/3}}$$
  The surface elevation at C.12 Samsen is physically governed by backwater profile integration starting from the downstream boundary $H_{\text{tide}}$. Because water depth $y$ increases during storm surge ($H_{\text{tide}} = +2.40\text{ m}$ MSL), cross-sectional area $A$ expands, which suppresses flow velocity and reduces the friction slope $S_f$. Therefore:
  $$\frac{\partial (\Delta H)}{\partial H_{\text{tide}}} < 0$$
  Treating head loss as purely additive ($\Delta H = c_1 \cdot Q^{1.28}$) assumes complete independence between tidal stage and discharge friction losses.
- **Proposed Solution**:
  Implement an interacting friction term calibrated against a 1D hydraulic backwater model (e.g., HEC-RAS):
  $$\Delta H = \frac{c_1 \cdot (Q / 1000)^{1.5}}{(H_{\text{tide}} + d_0)^{1.2}}$$
  where $d_0$ represents channel depth below datum.

---

### [F-07] Benchmark Classification Mismatch in Compound Risk Summary
- **Location**: `analysis/compound_flood_risk.py:100-106`, `analysis/compound_flood_risk.py:67-74`
- **Empirical Evidence**:
  Benchmark scenario 3 (`q_bangsai = 2250`, `tide_msl = 2.40`) calculates `c12_stage_msl_m = 2.85`.
  The floodwall crest is $2.80\text{ m}$ MSL; line 73 defines `else: risk = "critical"` for stages $>2.70\text{ m}$.
  However, line 105 sets status: `"เข้าสู่ระดับเตือนภัยสีส้ม (2.84 ม.) ชุมชนริมแม่น้ำต้องเฝ้าระวังสูงสุด"`.
- **Hydraulic & Data Science Critique**:
  Direct contradiction between the code's automated classification (Critical / Red) and the hardcoded status string (Warning / Orange).
- **Proposed Solution**:
  Update line 105 to: `"เข้าสู่ระดับวิกฤตล้นคันกั้นน้ำ (2.85 ม. สันคัน 2.80 ม.) ต้องเสริมแนวกระสอบทรายทันที"`.

---

### [F-08] Synthetic Inflow Hydrograph and Arbitrary Attenuation in CP2 Counterfactual Simulation
- **Location**: `analysis/goal7_counterfactual_simulation.py:75-77`, `analysis/goal7_counterfactual_simulation.py:96-105`
- **Empirical Evidence**:
  Lines 96–105:
  ```python
  n_days_54 = 122
  t_54 = np.linspace(0, math.pi, n_days_54)
  inflow_2554 = 2200.0 + 2486.0 * (np.sin(t_54) ** 1.3)
  inflow_2554 += np.random.normal(0, 45.0, n_days_54)
  ```
  Lines 75–77:
  ```python
  # ที่อยุธยา แม่น้ำกว้าง ~250 ม. v ~ 1.5 ม./วิ -> B*v ≈ 375 ม²/วิ -> ลดได้ ~dQ / 375
  peak_stage_reduction_m = peak_q_reduction / 1100.0  # ปรับเทียบ rating curve ช่วงน้ำหลากทุ่ง
  ```
  Lines 149–150:
  ```python
  "share_of_excess_flood_pct": round(res_54_600["total_diverted_mcm"] / 11000.0 * 100.0, 1)
  ```
- **Hydraulic & Data Science Critique**:
  The 2011 counterfactual claims (4,394.5 MCM diverted, 40.0% excess volume absorbed, 0.53 m stage reduction) are based on a mathematically generated sine curve rather than actual historical discharge records from C.13 and S.26. The 0.53 m stage reduction is obtained by dividing by an arbitrary factor of `1100.0` (nearly triple the physical channel conveyance $B \cdot v \approx 375\text{ m}^2\text{/s}$ without routing justification). The excess flood volume denominator (`11,000 MCM`) is hardcoded.
- **Proposed Solution**:
  1. Load actual daily gauged flows from 2011 (`data/23_rid_swoc/` or RID historical yearbook tables).
  2. Replace the empirical divisor with hydrodynamic rating curves extracted from the surveyed C.35 / Ayutthaya cross-sections.

---

### [F-09] Hardcoded Number Discrepancies in Plot Titles
- **Location**: `analysis/goal7_counterfactual_simulation.py:199`, `analysis/goal7_counterfactual_simulation.py:211`
- **Empirical Evidence**:
  Line 199: `ax1.set_title("ก) การจำลองตัดยอดน้ำหลากมหาอุทกภัยปี 2554 (ผันน้ำเลี่ยงอยุธยา-กทม. ได้ 3,695 ล้าน ลบ.ม.)", ...)`
  Output in JSON: `res_54_600["total_diverted_mcm"] = 4394.5`.
  Line 211: `ax2.set_title("ข) การจำลองตัดยอดน้ำหลากระลอกปลาย ก.ย. 2569 (ผันน้ำ 756 ล้าน ลบ.ม. ป้องกันน้ำล้นตลิ่งได้สมบูรณ์)", ...)`
  Output in JSON: `res_69_600["total_diverted_mcm"] = 215.8`.
- **Hydraulic & Data Science Critique**:
  Internal numeric discrepancy between generated graphics and generated JSON artifacts.
- **Proposed Solution**:
  Make titles dynamic:
  ```python
  ax1.set_title(f"ก) การจำลองตัดยอดน้ำหลากมหาอุทกภัยปี 2554 (ผันน้ำเลี่ยงอยุธยา-กทม. ได้ {res_54_600['total_diverted_mcm']:,.0f} ล้าน ลบ.ม.)", fontsize=11, fontweight="bold")
  ax2.set_title(f"ข) การจำลองตัดยอดน้ำหลากระลอกปลาย ก.ย. 2569 (ผันน้ำ {res_69_600['total_diverted_mcm']:,.0f} ล้าน ลบ.ม. ป้องกันน้ำล้นตลิ่งได้สมบูรณ์)", fontsize=11, fontweight="bold")
  ```

---

### [F-10] Reservoir Surcharge Storage Terminology vs. Structural Overtopping
- **Location**: `analysis/goal6_pasak_24y_baseline.py:25-27, 109-114`
- **Empirical Evidence**:
  `NORMAL_CAP = 871.5` MCM, `MAX_CAP = 1036.16` MCM.
  For 2010 (BE 2553):
  `peak_storage_mcm: 1177.22`, `peak_pct_normal: 135.1%`.
- **Hydraulic & Data Science Critique**:
  In dam engineering standards (USBR / ICOLD / RID), storage above Normal Conservation Storage ($871.5\text{ MCM}$) utilizes designed Surcharge Storage up to the Maximum Water Level (MWL, $1,036.16\text{ MCM}$ at +43.0 m MSL). Storing $1,177.22\text{ MCM}$ utilizes the emergency freeboard retention zone below the dam crest (+44.5 m MSL). Calling this "135.1%" without explicit structural definition can lead technical reviewers or legal auditors to conflate surcharge storage with structural dam crest overtopping.
- **Proposed Solution**:
  Explicitly define three distinct storage zones in `pasak_24y_summary.json` and report tables:
  1. Active Conservation Storage ($871.5\text{ MCM}$)
  2. Designed Flood Surcharge Pool ($1,036.16\text{ MCM}$)
  3. Emergency Freeboard Buffer ($1,036.16 - 1,200\text{ MCM}$ below crest +44.5 m MSL).

---

## 4. Verified Invariants (Passed Spot-Checks)

1. **System Integrity & Verification Suite**:
   - `python tools/verify_all.py` executed cleanly with exit code 0.
   - Catalog check (`catalog.py check`): 100% of all registered reports, canonical files, builders, docs, and datasets exist on disk.
   - SHA-256 raw data verification (`verify_data_integrity.py --quick`): 0 hash mismatches.
   - Documentation & Thai linting (`pytest tests/test_thai_language_lint.py`): 10/10 tests passed; 0 banned colloquialisms or collision typos found.
2. **RID Surveyed Cross-Section Geometry**:
   - Station Ny.7 (สะพานเทศบาลนครนายก): Surveyed profile verified against `data/19_rid_cross_sections/raw/Ny.7_2025.xlsx` and `manifest.md`. Thalweg elevation $-2.396\text{ m}$ MSL confirmed at offset 50.0 m. Left crest $+8.213\text{ m}$ MSL, right crest $+8.919\text{ m}$ MSL confirmed.
   - Station Ny.1B (บ้านเขานางบวช): Thalweg $+2.233\text{ m}$ MSL at offset 50.0 m; crest $+10.826\text{ m}$ MSL confirmed.
3. **Manning Hydraulic Geometry Calculations**:
   - Cross-sectional numerical integration (`analysis/rid_cross_section_hydraulics.py`): Correctly integrates wetted perimeter $P$ excluding free surface width (preventing artificial hydraulic radius doubling). Bankfull capacity $666.3\text{ m}^3\text{/s}$ at Ny.1B and $617.4\text{ m}^3\text{/s}$ at Ny.7 verified against Manning formulation ($n = 0.0437$).
4. **Khun Dan Dam 22-Year Mass Balance**:
   - `data/23_rid_swoc/raw/khundan_dam_history_2005_2026.json` September 2026 mass balance: Inflow $145.09\text{ MCM}$, Outflow $103.60\text{ MCM}$, Net Flux $+41.49\text{ MCM}$, Storage delta $+34.97\text{ MCM}$. Residual ($6.52\text{ MCM}$, $\approx 4.5\%$) matches regional reservoir evaporation and seepage allowances.
5. **Chao Phraya 2 Alignment & Water Chart Overlay**:
   - Canal dimensions: Length 135.655 km (new reach), design capacity $600\text{ m}^3\text{/s}$, and cross-structures (34 natural stream crossing siphons) verified against EIA 2026 records.
   - ONWR Water Chart spatial intersection: 16.8 km (47% of Nakhon Nayok reach) located inside official floodway zones verified.

---

## 5. Information Gaps & Required Field Data

1. **Khlong 29 Inverted Siphon Capacity Deficit (`khlong29_explanation`)**:
   At chainage km 53.8, the CP2 siphon design capacity is only $5\text{ m}^3\text{/s}$, whereas the natural design flood discharge of Khlong 29 is $36\text{ m}^3\text{/s}$. Official EIA documents do not explain where the remaining $31\text{ m}^3\text{/s}$ will drain when CP2 is operating at full capacity.
2. **Hourly Gate Operation Records for Chao Phraya & Rama VI Regulators**:
   Actual gate opening/closing logs and internal telemetry discharge ratings for C.13 (Chao Phraya Dam) and Rama VI Dam during late September 2026 are not accessible via open public APIs (only composite daily averages are provided via SWOC).
3. **Tidal Sluice Barrier Gate Schedules at Gulf Outlets**:
   Operational discharge coefficients and sluice opening schedules for coastal regulators at the mouth of the Chao Phraya, Bang Pakong, and Tha Chin rivers during extreme spring tides (+2.40 to +2.50 m MSL) remain unreleased.
4. **Sub-Daily Riverbed Bathymetry Between Ny.1B and Ny.7**:
   While bridge cross-sections are available, continuous reach bathymetry (1D river centerline profiles and bridge pier constriction dimensions) is unavailable, requiring estimated bed slopes ($S_0 = 0.00035$).
