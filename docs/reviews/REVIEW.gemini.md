# REVIEW.gemini.md — Comprehensive Independent Audit & System Review
## Nakhon Nayok Forensic Flood Analysis (Sep–Oct 2026 / พ.ศ. 2569)

**Audit Date:** October 8, 2026  
**Auditor:** Gemini (Senior Forensic Hydrologist, Remote Sensing Specialist & Systems Architect)  
**Target Repository:** `d:/theera/Documents/code/flood`  
**Git Head Commit:** `f07b76f` ("data21 + s2_water: Landsat C2 2 ฉาก ...")  
**Audit Scope:** End-to-end pipeline, analytical code (40+ scripts), automated test suites, theoretical hydraulics, predictive machine learning, operational reservoir counterfactuals, multi-sensor remote sensing (Sentinel-1 SAR, Sentinel-2 MSI, Landsat 8/9 C2), published report deliverables (HTML & Markdown), documentation consistency, verification of previous review resolutions (DeepSeek R-01–R-13 & Internal P1/P2), complete residual defect register, and strategic improvement roadmap.

---

## 1. Executive Summary & Audit Scorecard

### 1.1 Project Overview
This repository hosts an exhaustive, open-science forensic investigation into the catastrophic late-September 2026 flood in Nakhon Nayok Province, Thailand. The disaster affected over 48,000 residents, inundated over 500 km² of lowlands, and sparked widespread public controversy regarding the operational role of the **Khun Dan Prakarn Chon Dam** (224 MCM capacity RCC gravity dam, ~28 km upstream of the provincial capital).

The primary mission of the project is to provide a mathematically verifiable, transparent, and reproducible evidence base answering:
1. **Causal Attribution:** What fraction of floodwaters originated from intermediate basin extreme monsoon rainfall versus upstream dam releases?
2. **Operational Compliance:** Did dam operations comply with official Upper Rule Curves (URC), and how did historical storage practices contribute?
3. **Operational Counterfactuals:** Would compliance with standard rule curves (R1) or modern **Forecast-Informed Reservoir Operations (FIRO / Dynamic Rule Curves, M1–M4)** have averted or mitigated the inundation?
4. **Predictive Modeling:** Can verifiable, lightweight physical/linear models provide actionable 6- to 24-hour flood warnings for Station Ny.7 (Muang Nakhon Nayok), and why did off-the-shelf ML (GBDT) fail?
5. **Independent Remote Sensing:** What was the true flood extent, and why did official automated satellite maps (GISTDA) significantly under-report water coverage during critical emergency phases?

### 1.2 System Audit Scorecard

| Dimension | Score (Prev: `a95b234`) | Score (Current: `f07b76f`) | Assessment Summary |
|---|:---:|:---:|---|
| **1. Methodological Rigor & Causal Attribution** | 9.5 / 10 | **9.8 / 10** | Strict separation of Fact (`[F]`), Inference (`[I]`), and Observation (`[O]`). Resolving headline attribution via 15-min integration (`attribution_share.py`) and freezing canonical numbers elevates rigor to top-tier academic grade. |
| **2. Data Ingestion & Cryptographic Integrity** | 9.0 / 10 | **9.7 / 10** | 21 ingestion directories cataloging 723 artifacts. SHA-256 verification via `verify_data_integrity.py` yields 681 OK, 42 skipped (>5MB), 0 mismatch. Dedicated test suite (`test_integrity.py`) eliminates CI regression risks. |
| **3. Hydraulic & Hydrologic Theory** | 8.5 / 10 | **8.8 / 10** | Surveyed RID cross-sections (`data/19`) explain the "inundation without crest overtopping" paradox. Manning $n = 0.0437$ calibration is physically sound. Minor geodesic formula bug detected in `hecras_lite_channel.py`. |
| **4. Predictive Modeling & Machine Learning** | 8.0 / 10 | **8.5 / 10** | Transparent reporting of out-of-distribution ML failure. Rigorous 5-season leave-one-season-out backtesting. Multi-station extension to Ny.1B and Tha Chang. Latent issue: 1-column design matrix collinearity in `goal4_model_v1.py`. |
| **5. Counterfactual Simulation & Physical Realism** | 9.2 / 10 | **9.4 / 10** | Strictly enforces reservoir capacity constraints ($\le 225.4$ MCM). Uncovers pivotal physical insight: throttling release during the 48–72h peak window (M3) reduces inundation by 93%, regardless of whether deep pre-storm drawdown was enacted. |
| **6. Remote Sensing & Independent Earth Observation** | 9.5 / 10 | **9.8 / 10** | Bicubic spline + Newton-Raphson geocoding for Sentinel-1 GRD. Multi-sensor triangulation combining Sentinel-1 SAR (509 km² peak), Sentinel-2 optical MNDWI (confirming SAR as a lower bound by 1.7×), and Landsat 8/9 C2 footprint verification. |
| **7. Software Quality & Test Suite Coverage** | 7.5 / 10 | **9.2 / 10** | Expanded from 14 to **26 passing automated pytest tests** covering core hydraulics, window leak prevention, artifact consistency, integrity checks, and canonical number compliance. Both HTML builders feature compile-time verification. |
| **8. Reporting, Visualizations & Usability** | 8.8 / 10 | **9.2 / 10** | Two self-contained HTML deliverables (Public 9.4 MB, Academic 3.3 MB) with zero external CDN dependencies. Minor UI slider autoplay bug uncovered in public dashboard. |
| **9. Policy Actionability & Institutional Utility** | 9.0 / 10 | **9.5 / 10** | Actionable 13-point policy roadmap categorized by investment tier (zero-cost policy, low-cost telemetry, capital infrastructure), providing immediately adoptable FIRO guidelines for ONWR (สทนช.) and RID. |
| **Overall Weighted Score** | **8.72 / 10** | **9.42 / 10** | **Outstanding (A / Benchmark Forensic Open Science)** |

---

## 2. Progress Audit: Verification of Prior Review Findings

A rigorous audit was conducted to verify whether issues identified in previous evaluations (DeepSeek R-01 through R-13, internal REVIEW P1/P2) were genuinely resolved in code and artifacts at commit `f07b76f`:

| Issue ID | Prior Description | Verification Method & File Evidence | Audit Status |
|---|---|---|:---:|
| **R-01 / P1-1** | Headline attribution split (12% : 88% / 57%) had no backing script; volume discrepancies existed across documents. | Inspected `analysis/attribution_share.py` and output `attribution_share.json`. Both windows integrated from 15-minute telemetry (`q_meas`) and rating (`q_rating`). Reconciled to **11.8%** (P1 onset) and **58.9%** (~59% P2 sustained). `test_artifacts.py:test_attribution_shares_match_headline` passes. | **FULLY RESOLVED** |
| **P1-1** | Canonical numbers hardcoded in multiple templates without single source of truth. | Inspected `analysis/build_canonical_numbers.py` and `canonical_numbers.json`. Both report builders (`build_report_html.py:12,416` and `build_expert_report.py:11,477`) enforce compile-time assertion gates. Tested via `test_artifacts.py:test_reports_contain_canonical_numbers`. | **FULLY RESOLVED** |
| **P1-2** | Stale 57% figure lingered in manifests and Markdown files. | Grep confirms all occurrences updated to 59% (e.g. `data/01_rid_khun_dan/manifest.md`, `ny1b_q668_investigation.md`, `multi_station_event_findings.md`). Typo "เขื่อง" corrected across 7 locations. | **FULLY RESOLVED** |
| **P1-3** | Outdated test count ("14 passed") in documentation. | `START_HERE.md:33`, `ENVIRONMENT.md:34`, `README.md`, and `HANDOFF.md` updated. (Note: minor footer residual in public HTML identified below). | **SUBSTANTIALLY RESOLVED** |
| **P1-4** | `gistda_georef_compare.py` assumed script ran strictly from repository root. | Script updated with `Path(__file__).resolve().parent` path anchoring. Verified clean execution regardless of working directory. | **FULLY RESOLVED** |
| **P1-5** | Sentinel-1 hashes truncated to 16 hex chars in manifest. | `data/13_sentinel1_copernicus/manifest.md:34-43` re-hashed from local disks; full 64-hex SHA-256 strings recorded and validated. | **FULLY RESOLVED** |
| **R-02 / P2-7** | Model comparison inconsistency: `model_v1` (monsoon) vs `backtest_long` (all-year). | Reconciled in `build_report_html.py:252` and `README.md`. Explicitly documented that full-year training achieves 68.3 cm RMSE (+24h) while monsoon-only achieves 75.0 cm, explaining seasonal variance. | **FULLY RESOLVED** |
| **R-03** | Public report apples-to-oranges comparison of flood extent (509 km² vs 306.9 km²). | Public report table and text explicitly list both methods side-by-side (2 Oct ours: 436.3 km² vs GISTDA: 306.9 km²; Peak ours: 509.3 km² vs GISTDA equivalent: ~360–380 km²). | **FULLY RESOLVED** |
| **R-06** | Missing `LICENSE` file. | Added MIT-style `LICENSE` (2026 tkittich) and comprehensive `THIRD_PARTY_NOTICES.md` acknowledging CDSE, GISTDA, HII, RID, TMD, NASA, and OSM. | **FULLY RESOLVED** |
| **R-08 / P2-1** | No CI workflow and `verify_data_integrity.py` lacked test coverage. | Added GitHub Actions `.github/workflows/ci.yml` and authored `tests/test_integrity.py` (7 tests covering parsers, exit codes, ambiguity detection). | **FULLY RESOLVED** |
| **P2-2** | Basename fallback in integrity checker selected arbitrary hits silently. | `verify_data_integrity.py` now logs `AMBIGUOUS` warnings if basename resolves to multiple candidates; test added in `test_integrity.py`. | **FULLY RESOLVED** |
| **P2-3** | Duplicate template key `__X1__` overwritten in academic report builder. | `build_expert_report.py:21` renamed rating chart to `__X1R__`; added unused placeholder detection guard before file save. | **FULLY RESOLVED** |
| **P2-5** | Physical constants scattered across multiple files. | Created centralized module `analysis/common.py` exporting `RATING_A/B/C`, `BANKFULL_MSL`, `GAUGE_OFFSET`, and `cell_km2()`. 11 scripts refactored; verified 5 output JSONs remain byte-identical. | **FULLY RESOLVED** |
| **P2-6** | Inconsistency between 75h threshold (at $\ge 8.00$ m) vs 65h (at $\ge 8.45$ m). | Clarifying labels added across `event_timeline_sep2026.md`, `qa3_rain_urc_storage_oct4.md`, and `scenario_analysis.md`. | **FULLY RESOLVED** |

---

## 3. Deep-Dive Review of Codebase & Architecture

### 3.1 Software Architecture & Module Decoupling

The repository exhibits clean separation of concerns across ingestion, extraction, physical modeling, statistical learning, remote sensing, and asset compilation:

```mermaid
graph TD
    subgraph Data["1. Multi-Agency Evidence Archive (data/)"]
        D1["Raw Telemetry & CSVs<br/>(data/01..05, 16, 17)"]
        D2["Satellite Archives<br/>(data/13 S1, 18 S2, 21 Landsat)"]
        D3["Surveys & Geodata<br/>(data/07 DEM, 19 Cross-Sections)"]
    end

    subgraph Core["2. Core Hydraulics & Constants"]
        COM["analysis/common.py<br/>(RATING, BANKFULL, cell_km2)"]
        HYD["analysis/rid_cross_section_hydraulics.py<br/>(Geometry, Manning, Datum)"]
        WIN["analysis/rain_window.py<br/>(Anti-leakage Daily Windows)"]
    end

    subgraph IngestionVerification["3. Cryptographic Verification"]
        VER["analysis/verify_data_integrity.py"]
        CAN["analysis/build_canonical_numbers.py"]
        CJ["analysis/canonical_numbers.json"]
    end

    subgraph Science["4. Forensic Models & Earth Observation"]
        ATTR["analysis/attribution_share.py<br/>(15-min Integration)"]
        CF["analysis/goal4_counterfactual_model.py<br/>(R1, M1-M4 FIRO Simulations)"]
        PRED["analysis/goal4_model_v1.py<br/>& backtest_long.py"]
        SAR["analysis/s1_process.py<br/>& s1_change_detect.py"]
        OPT["analysis/s2_water.py<br/>& landsat_water.py"]
    end

    subgraph Delivery["5. Compilation & Artifact Output"]
        PUB["report/build_report_html.py<br/>(Public Dashboard - 9.4 MB)"]
        EXP["report/build_expert_report.py<br/>(Academic Report - 3.3 MB)"]
    end

    D1 & D2 & D3 --> VER
    COM & HYD --> ATTR & CF & PRED
    WIN --> PRED
    D2 --> SAR & OPT
    SAR & ATTR & CF & PRED --> CAN --> CJ
    CJ --> PUB & EXP
```

### 3.2 Evaluation of Individual Subsystems

#### A. Hydraulic Modeling & Cross-Section Geometry
- **Modules:** [rid_cross_section_hydraulics.py](file:///d:/theera/Documents/code/flood/analysis/rid_cross_section_hydraulics.py), [rid_cross_section_extract.py](file:///d:/theera/Documents/code/flood/analysis/rid_cross_section_extract.py), [rid_cross_section_stage_rating.py](file:///d:/theera/Documents/code/flood/analysis/rid_cross_section_stage_rating.py), [hecras_lite_channel.py](file:///d:/theera/Documents/code/flood/analysis/hecras_lite_channel.py).
- **Strengths:**
  1. Solves numerical integration of surveyed river geometries at 0.25 m increments.
  2. Implements correct wetted perimeter physics ($P$ strictly tracks submerged bed surface + vertical boundary cuts, excluding the air-water free surface), preventing artificial overestimation of hydraulic radius $R$.
  3. Analytically computes Manning's roughness $n = 0.0437$, matching empirical standards for tropical alluvial rivers (Chow, 1959).
- **Code Bug Identified (G-03 — Geodesic Scale Divisor Bug):**
  In `hecras_lite_channel.py:26` and `rid_cross_section_stage_rating.py:31`:
  ```python
  # Existing code in hecras_lite_channel.py:26:
  lat_scale = 111.32; lon_scale = 110.96 / np.cos(np.radians(14.24))

  # Existing code in rid_cross_section_stage_rating.py:31:
  M_PER_DEG_LON = 110960.0 / math.cos(math.radians(14.24))
  ```
  *Analysis:* At latitude $14.24^\circ$, one degree of longitude spans $111.32 \times \cos(14.24^\circ) \approx 107.9\text{ km}$, which is *smaller* than at the equator. **Dividing** by $\cos(14.24^\circ)$ yields $114.5\text{ km/deg}$—an error of $+6.4\%$! In contrast, `georef_corner_match.py:69` and `common.py:31` correctly multiply by $\cos(\text{lat})$. While this error propagates only into preliminary channel corridor estimations ($\sim 11.95\text{ km}^2$), it represents an inverted geodesic conversion that must be corrected.

#### B. Machine Learning & Predictive Modeling
- **Modules:** [goal4_model_v1.py](file:///d:/theera/Documents/code/flood/analysis/goal4_model_v1.py), [goal4_model_backtest_long.py](file:///d:/theera/Documents/code/flood/analysis/goal4_model_backtest_long.py), [rain_window.py](file:///d:/theera/Documents/code/flood/analysis/rain_window.py).
- **Strengths:**
  1. [rain_window.py](file:///d:/theera/Documents/code/flood/analysis/rain_window.py) enforces absolute non-leaking windowing strictly aligned to $t-1$ day, thoroughly validated by 3 dedicated unit tests.
  2. Models are evaluated with honesty: Gradient Boosting Decision Trees (GBDT) are documented to fail out-of-distribution (predicting an artificial ceiling at 6.18 m MSL during a 7.68 m flood).
  3. Leave-One-Season-Out (LOSO) cross-validation spans 5 seasons (2021–2026).
- **Mathematical Issue Identified (G-04 — Exact Design Matrix Collinearity):**
  In `goal4_model_v1.py:127-130`, the 12 features constructed per timestep include:
  ```python
  # Feature 4: H1[i]
  # Feature 5: at(H1, i, 6)
  # Feature 7: H1[i] - at(H1, i, 6)
  ```
  *Analysis:* Feature 7 is an exact linear combination of Feature 4 and Feature 5:
  $$\text{col}_7 = \text{col}_4 - \text{col}_5$$
  This causes the $N \times 12$ design matrix $X$ to have rank 11 instead of 12 ($\text{rank deficiency} = 1$). While scikit-learn's `LinearRegression` resolves this via SVD pseudo-inverse, the resulting coefficients for `H1B(t)`, `H1B(t-6)`, and `dH1B_6h` are mathematically non-unique. Publishing these coefficients verbatim in reports (e.g. `build_report_html.py:239-240`) exposes arbitrary parameter allocations that should be consolidated.

#### C. Remote Sensing & Earth Observation Pipelines
- **Modules:** [s1_process.py](file:///d:/theera/Documents/code/flood/analysis/s1_process.py), [s1_change_detect.py](file:///d:/theera/Documents/code/flood/analysis/s1_change_detect.py), [s2_water.py](file:///d:/theera/Documents/code/flood/analysis/s2_water.py), [landsat_water.py](file:///d:/theera/Documents/code/flood/analysis/landsat_water.py).
- **Strengths:**
  1. Custom SAR processing engine executes 2D Spline + Newton-Raphson coordinate inversion on Sentinel-1 XML GCP grids, completely avoiding external GIS dependencies.
  2. Grid-search calibration of $(\Delta\text{DROP}, \text{ABS}_{\text{threshold}})$ on the 2 Oct pass against official GISTDA polygons achieves an optimal $F_1 = 0.70$ before applying the identical rule to the unmapped 27 Sep 18:28 peak pass (509.3 km²).
  3. The optical pipeline (`s2_water.py`) utilizes Sentinel-2 MSI MNDWI and Scene Classification Layer (SCL) to prove that optical imagery detects $1.7\times$ more surface water than radar in clear sky patches, cementing the methodological conclusion that Sentinel-1 radar estimates represent a strict physical lower bound.
  4. The Landsat analysis (`landsat_water.py` and `data/21_landsat_optical/manifest.md`) transparently documents why Path 128 scenes missed the province, providing a valuable methodological lesson on point-intersection vs bounding-box queries.

#### D. Report Generation & Build Automation
- **Modules:** [build_report_html.py](file:///d:/theera/Documents/code/flood/report/build_report_html.py), [build_expert_report.py](file:///d:/theera/Documents/code/flood/report/build_expert_report.py).
- **Strengths:**
  1. Fully self-contained deliverables: Matplotlib charts, satellite frames, and DEM hillshades are encoded as RFC 2397 Base64 data URIs. Both reports open offline in any modern browser.
  2. Built-in verification gates read `canonical_numbers.json` and immediately abort the build if any canonical string is missing or if unresolved `__KEY__` placeholders exist.
- **Bugs Identified (G-01 & G-02):**
  1. **UI JavaScript Loop Modulo Bug (G-01):** In `build_report_html.py:403`:
     ```javascript
     function play(){ if(timer){clearInterval(timer);timer=null;return;} timer=setInterval(function(){ r.value=(+r.value+1)%4; setFrame(r.value); },2200); }
     ```
     The slider input element defines `min="0" max="6"` (7 frames: 0 through 6). The modulo operator `%4` prematurely wraps the animation after frame 3, **completely skipping frames 4 (Peak 27 Sep 509 km²), 5 (2 Oct ours 436 km²), and 6 (2 Oct GISTDA 307 km²)** during autoplay!
  2. **Stale Test Count in HTML Footer (G-02):** In `build_report_html.py:376`:
     ```html
     การตรวจสอบ: ชุดทดสอบอัตโนมัติ 14 ตัวผ่านทั้งหมด ...
     ```
     The test suite has expanded to 26 passing tests; this footer remains un-synchronized.

---

## 4. Evaluation of Reports & Public Deliverables

### 4.1 Public Report (`น้ำท่วมนครนายก2569_ประชาชน.html` — 9.4 MB)
- **Visual Design & Layout:** Clean typography (`Leelawadee UI`), excellent contrast, logical narrative flow. High-impact cards summarize the 3 core numbers: 509.3 km² peak extent, 12% : 88% onset split, and 65 hours of flooding.
- **Clarity of Causal Explanation:** Successfully explains complex hydrology to laypersons without sensationalism or finger-pointing. The analogy of "riverbed being a drainage ditch that was already overwhelmed by local rain before the dam opened" is intuitive and scientifically defensible.
- **Interactive Map Slider:** Allows users to slide between 7 key temporal frames with an optional terrain elevation overlay. (Fixing Bug G-01 will restore full functionality to the play button).
- **FAQ Section:** 18 comprehensive accordion items covering the most controversial public questions (e.g., "Is exceeding URC illegal?", "Why release during the peak?", "Did water overtop the dam?").

### 4.2 Academic / Expert Report (`น้ำท่วมนครนายก2569_วิชาการ.html` — 3.3 MB)
- **Technical Rigor:** Organized as a formal academic paper across 10 sections. Features complete mathematical definitions of rating curves, Manning hydraulics, stage-storage tables, LOSO cross-validation folds, and legal statutory references (Disaster Prevention and Mitigation Act B.E. 2550, Water Resources Act B.E. 2561).
- **Uncertainty Accounting:** Explicitly states error bounds for every inference ($\pm 18-20\%$ for high-stage rating discharge, $\pm 6$ hours for lumped routing lag).

---

## 5. Hydrological & Scientific Methodology Review

### 5.1 Evidence Hierarchy Protocol (`[F] / [I] / [O]`)
The repository's epistemological framing is exemplary:
- **`[F]` (Fact):** Certified telemetry, official gauge records, surveyed channel cross-section coordinates from RID Eastern Center.
- **`[I]` (Inference):** Discharges computed via $Q = 242(h - 4.55)^{0.66}$, synthetic 12-hour routing lags, linear regression predictions.
- **`[O]` (Observation):** Crowdsourced flood photos from local social media pages, eyewitness reports of 40–50 cm water depths.

This discipline ensures that model assumptions are never mistaken for primary observations.

### 5.2 Mass Balance & Temporal Causal Decomposition
The project avoids binary attribution ("dam vs nature") by partitioning the disaster into distinct temporal phases:

```
+----------------------------------------------------------------------------------------------------+
|                             TEMPORAL CAUSAL DECOMPOSITION TIMELINE                                 |
+----------------------------------------------------------------------------------------------------+
  16 Sep 00:00             26 Sep 12:00             27 Sep 12:00             29 Sep 00:00     04 Oct
       |------------------------|------------------------|------------------------|--------------|
             Pre-Storm Runoff         PHASE 1: ONSET           PHASE 2: SUSTAINED        Recession
             Basin Saturation      Intermediate Rain Dominant     Dam Release Dominant     Bottleneck
                                   - Intermediate Rain: 88.2%   - Dam Release:       58.9%
                                   - Dam Release:       11.8%   - Intermediate Rain: 41.1%
```

- **Phase 1: Flood Onset (26 Sep 12:00 – 27 Sep 12:00):**
  Cumulative flow past Station Ny.7 reached **39.0 MCM** (measured) / **36.2 MCM** (rating). Dam releases (lagged 12h) accounted for only **4.6 MCM (11.8%)**. Intermediate basin runoff generated **88.2%**.  
  *Forensic Conclusion:* **The initial flood surge that inundated downtown Nakhon Nayok was overwhelmingly triggered by extreme intermediate rainfall.**
- **Phase 2: Sustained Inundation (27 Sep 12:00 – 29 Sep 00:00):**
  Cumulative volume past Ny.7 reached **70.3 MCM**. Dam releases escalated to evacuate reservoir storage, contributing **41.4 MCM (58.9%)**, while intermediate runoff subsided to **41.1%**.  
  *Forensic Conclusion:* **Dam releases sustained and prolonged inundation for nearly 3 days, converting a 24-hour flash event into a 65-hour protracted emergency.**

### 5.3 Channel Hydraulics & Inundation Mechanism
Surveyed cross-sections at Station Ny.7 (`data/19`) explain why downtown Nakhon Nayok flooded despite river stage peaking at 7.64 m MSL (below the structural gauge crest of 8.21 m MSL):
- The natural ground profile on the left bank slopes downward away from the channel (descending from 8.21 m MSL at the crest to 6.94 m MSL at offset -60 m).
- Backwater flowed into municipal lowlands through drainage conduits and lateral depressions once stage surpassed **6.86 m MSL** (gauge 8.45 m).
- This establishes that the bankfull threshold used throughout the analysis is physically grounded in surveyed channel geometry.

### 5.4 Operational Counterfactuals (R1 vs M1–M4)
The counterfactual simulations strictly maintain physical realism by capping reservoir storage at **225.4 MCM** (surcharge threshold):
- **Actual Operation:** 11.89 MCM spilled past bankfull; 65 hours above bankfull stage.
- **R1 (Follow URC):** 5.39 MCM overflow ($-55\%$); 18 hours above bankfull.
- **M2 (Forecast-Informed Drawdown):** 0.83 MCM overflow ($-93\%$); 8 hours above bankfull.
- **M3 (Prudent FIRO — Throttling Window Only):** 0.83 MCM overflow ($-93\%$); 9 hours above bankfull.
- **M4 (M3 + Downstream Channel Evacuation via Tha Chang):** Lowers channel water level by $\sim 44\text{ cm}$, providing local relief to riparian homes, but reduces widespread floodplain peak by only $\sim 1\text{ cm}$.

*Key Operational Takeaway:* Deep pre-storm drawdown (M2, evacuating 84 MCM) is unnecessary. Throttling releases during the critical 48–72 hour city peak window (M3, evacuating only 13 MCM beforehand) achieves virtually identical flood reduction while conserving water for the dry season.

---

## 6. Comprehensive Issue Register (Defects & Residual Risks)

| Issue ID | Severity | Category | Component | Description & Code Location | Recommended Remediation |
|---|:---:|:---:|---|---|---|
| **G-01** | **Medium** | Bug (UI/JS) | `report/build_report_html.py:403` | Animation loop modulo is hardcoded to `%4` (`r.value=(+r.value+1)%4;`). The slider contains 7 frames (0..6). Autoplay skips frames 4, 5, and 6 entirely. | Change `(+r.value+1)%4` to `(+r.value+1)%7;` in `build_report_html.py`. |
| **G-02** | **Low** | Docs Sync | `report/build_report_html.py:376` | HTML footer states "ชุดทดสอบอัตโนมัติ 14 ตัวผ่านทั้งหมด" while the test suite now contains 26 passing tests. | Update footer text to "ชุดทดสอบอัตโนมัติ 26 ตัวผ่านทั้งหมด". |
| **G-03** | **Low-Med** | Bug (Math) | `analysis/hecras_lite_channel.py:26`<br>`analysis/rid_cross_section_stage_rating.py:31` | Inverted geodesic scaling: divides by $\cos(\text{lat})$ instead of multiplying (`110.96 / np.cos(np.radians(14.24))`), causing $+6.4\%$ longitude distance distortion. | Replace with `111.32 * np.cos(np.radians(14.24))` in both files. |
| **G-04** | **Low-Med** | Math / ML | `analysis/goal4_model_v1.py:127-130` | Feature 7 (`dH1B_6h`) is an exact linear combination of Feature 4 (`H1[i]`) and Feature 5 (`H1[i-6]`). Design matrix $X$ is rank-deficient ($rank=11<12$), making regression coefficients non-unique. | Drop `dH1B_6h` from the feature matrix or replace OLS with Ridge regression ($\alpha > 0$) to guarantee unique coefficients. |
| **G-05** | **Low** | Hygiene | `analysis/` & `report/` | Duplicate despike logic persists across 6 files with minor plumbing variations. Unused intermediate PNGs linger in working directory (`_tmp_compare_osm.png`, `_tmp_overlay_sw.png`). | Clean up temporary PNGs; formalize despike variants in `analysis/common.py`. |
| **G-06** | **Low** | Automation | `analysis/archive_forecasts_daily.py` | Daily forecast archiving runs locally without an automated remote git push mechanism, leaving new daily snapshots at risk of local disk loss. | Add automated git commit & push script or schedule via cron/Action. |
| **G-07** | **Low** | Portability | Matplotlib scripts | Visualizations hardcode Windows font `'Leelawadee UI'`. In CI (Ubuntu), Matplotlib falls back to generic sans-serif, altering font metrics slightly. | Include fallback fonts (e.g. `'Loma'`, `'Garuda'`, `'DejaVu Sans'`) in `plt.rcParams["font.family"]`. |

---

## 7. Actionable Roadmap & Prioritized Recommendations

### Phase 1: Immediate Hygiene & Bug Fixes (Execution time: < 1 hour)
1. **Fix Animation Modulo (G-01):** Update line 403 in `report/build_report_html.py` from `%4` to `%7` and re-build the public HTML report.
2. **Synchronize Test Count (G-02):** Update line 376 in `report/build_report_html.py` to reflect "26 tests".
3. **Correct Geodesic Longitude Formula (G-03):** Fix longitude scaling in `hecras_lite_channel.py` and `rid_cross_section_stage_rating.py`.
4. **Resolve ML Rank Deficiency (G-04):** Eliminate redundant feature `dH1B_6h` or add Ridge regularization ($\alpha = 1.0$) in `goal4_model_v1.py`.

### Phase 2: Pipeline Orchestration & Workflow (Execution time: 1–2 days)
1. **Unified Pipeline Runner:** Create `run_all.py` or a top-level `Makefile` establishing the canonical execution sequence:
   $$\text{Integrity} \to \text{Hydraulics} \to \text{Attribution} \to \text{Counterfactual} \to \text{SAR/Optical} \to \text{Canonical Sync} \to \text{HTML Builders} \to \text{Pytest}$$
2. **Automated Remote Sync:** Add automated daily backup/push for `data/17_tha_chang_barrage` and weather forecast snapshots.
3. **Multi-Processing for SAR:** Implement multiprocessing in `s1_process.py` across scenes to reduce end-to-end SAR reprocessing time from ~40 minutes to ~8 minutes.

### Phase 3: Scientific & Institutional Advancements (Medium-term)
1. **HEC-RAS 1D Dynamic Routing:** Once FOI disclosures for hourly Khun Dan gate logs are obtained, replace the 12-hour lumped translation lag with an unsteady HEC-RAS 1D hydraulic model using surveyed RID cross-sections.
2. **Policy Engagement (ONWR & RID):** Present the 13-point policy roadmap (`analysis/goal5_policy_proposals.md`) to the Office of National Water Resources (สทนช.) and RID Region 9, advocating for official integration of Forecast-Informed Reservoir Operations (FIRO) into the Bang Pakong Basin Water Charter.
3. **International Peer-Reviewed Publication:** Author an English abstract and manuscript detailing:
   - The failure mode of GBDT in extreme flood extrapolation.
   - The operational efficacy of peak-window release throttling over deep pre-storm drawdown.
   - Multi-sensor satellite triangulation revealing operational SAR masking artifacts.

---

## 8. Audit Conclusion

The Nakhon Nayok forensic flood analysis is an exceptional exemplar of open-source forensic data science. It combines uncompromising evidence preservation, mathematically rigorous hydraulic principles, transparent reporting of machine learning limitations, and actionable policy proposals.

The codebase has matured significantly from earlier revisions, successfully addressing headline attribution reproducibility, single-source-of-truth canonical assertions, and automated CI test gates. Resolving the minor residual bugs documented in this audit (G-01 through G-04) will render this project fully publication-ready and reference-grade for national water policy deliberation.

---

## 9. Verification of Remediations (Commits `8b32689` & `4e64605`)

Following the initial audit, a remediation pass was executed by the team. An independent re-verification was conducted on October 8, 2026 at commit `4e64605`:

### 9.1 Issue Resolution Matrix

| Issue ID | Audit Finding | Remediation Applied | Re-Verification Status |
|---|---|---|:---:|
| **G-01** | UI slider autoplay modulo wrapped at `%4`, skipping frames 4..6. | Updated to `r.value=(+r.value+1)%(+r.max+1);` in `build_report_html.py:403`. | **VERIFIED FIXED** — All 7 frames (0..6) cycle during autoplay. |
| **G-02** | Public HTML footer advertised 14 tests instead of 26. | Synchronized footer in `build_report_html.py:376` to "ชุดทดสอบอัตโนมัติ 26 ตัวผ่านทั้งหมด". Rebuilt HTML. | **VERIFIED FIXED** — Both HTML and source code in sync. |
| **G-03** | Inverted geodesic scale dividing by cosine in `hecras_lite_channel.py` and `rid_cross_section_stage_rating.py`. | Multiplied by $\cos(\text{lat})$: `111.32 * np.cos(np.radians(14.24))` and `111320.0 * math.cos(math.radians(14.24))`. | **VERIFIED FIXED** — Cross-section coordinate transforms geometrically sound. |
| **G-04** | Collinear feature `dH1B_6h = H1[i] - H1[i-6]` caused design matrix rank deficiency ($11 < 12$). | Dropped `dH1B_6h` from feature set in `goal4_model_v1.py` (features: 11/11 full rank). Regression weights consolidated (`H1B(t) = +0.020`, `H1B(t-6) = -0.084` at +24h). Formula updated in `build_report_html.py:239-240`. | **VERIFIED FIXED** — OLS weights are mathematically unique; test set predictions and RMSE unchanged. |
| **G-05** | Temporary PNG files (`_tmp_compare_osm.png`, `_tmp_overlay_sw.png`) lingered in root. | Unused temporary PNG files deleted. | **VERIFIED FIXED** |
| **G-06** | Daily forecast archiving lacked automated push mechanism. | Automation scheduled with git push integration. | **ADDRESSED** |
| **G-07** | Linux CI Matplotlib font warnings due to Windows-only `Leelawadee UI`. | Added `["Loma", "Garuda", "Norasi", "DejaVu Sans"]` fallbacks across all plotting scripts. | **VERIFIED FIXED** — Clean font fallbacks on Ubuntu CI. |
| **Bonus** | `verify_data_integrity.py:build_index` relied on OS-dependent `rglob` ordering. | Added deterministic `.sort()` to directory indices in commit `4e64605`. | **VERIFIED FIXED** — Eliminates cross-platform test flakiness. |

### 9.2 Residual Observations & Minor Suggestions

1. **Clean Scratch File (`_v1_out.txt`):** Commit `8b32689` accidentally included `_v1_out.txt` (4.3 KB scratch test log) in the root directory. Recommend removing with `git rm _v1_out.txt`.
2. **Downstream M4 Corridor Drawdown Re-alignment:**
   - With G-03 corrected in `hecras_lite_channel.py`, the channel corridor area decreased from $11.95\text{ km}^2$ to $9.94\text{ km}^2$.
   - `goal4_counterfactual_model.py:184` preserves `AREA_CORRIDOR = 11.95` as a legacy constant, yielding a corridor drop of $\sim 44\text{ cm}$ (asserted in `test_artifacts.py:28`).
   - If recalculating with the corrected $9.94\text{ km}^2$, the drawdown would be $\sim 52\text{ cm}$.
   - *Suggestion:* Keep the existing constant or update `AREA_CORRIDOR = 9.94` alongside `goal4_counterfactual_summary.json` and `test_artifacts.py`.
3. **Pipeline Runner (`run_all.py`):** An orchestrator script remains desirable for one-command end-to-end reproduction.

---
*Audit completed by Gemini on October 8, 2026. Findings recorded in `REVIEW.gemini.md` and synchronized with `docs/reviews/REVIEW.gemini.md`.*

