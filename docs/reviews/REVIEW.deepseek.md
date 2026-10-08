# REVIEW.deepseek.md — Independent Technical Review

> **Project:** Forensic evidence archive + causal analysis of the Nakhon Nayok flood, late September 2026 (B.E. 2569)
> **Repository:** `D:\theera\Documents\code\flood` · branch `main` · commit reviewed: **`5a7ced8`** (working tree clean)
> **Reviewed:** 6 October 2026
> **Reviewer:** DeepSeek-V4.1-Flash (Sift), acting as an independent reviewer — not the author of any code or document in this repo
> **Method:** read every document and script; **ran** the test suite; **re-derived and re-ran** the Goal-4 model pipeline to check its central claim; audited manifests, hashes, git state and data hygiene. Every quantitative claim below was executed or read from a primary file, not inferred.
> **Relation to `REVIEW.gemini.md`:** that file is a separate, earlier (Thai) review. This review is independent and **corrects at least one number it states** (§13). Read both; they are not duplicates.

---

## 0. How this review was done (so you can re-check it)

| Step | Command / method | Result |
|---|---|---|
| Read scope + standards | `README.md`, `docs/{METHODS,DATA_SOURCES,DATA_DICTIONARY,ANALYSIS_PLAN,HANDOFF}.md` | see §3–§6 |
| Read all analysis code | 24 `.py` files in `analysis/` + `report/` | see §7–§9 |
| Run the test suite | `python -m pytest tests/ -q` | **5 passed in 0.01 s** — but the tests are vacuous (§10 F-04) |
| Verify the Goal-4 model | re-implemented `goal4_model_v1.py`'s feature build; reproduced shipped RMSEs exactly, then re-ran with corrected features | **confirmed defect F-01** (§7.2) |
| Check manifests / hashes | loop over `data/*/manifest.md` | 4 folders missing manifest; 4 manifests missing SHA-256 (§10 F-05) |
| Check git state | `git log`, `git status`, `git ls-files` | clean; 984 tracked files; 54 commits over 2 days |
| Check portability | grep for absolute paths, `__file__` usage, packaging files | 4 scripts hardcode `D:\theera\...`; no `pyproject.toml` (§8) |

Environment note that matters for reproduction: the **managed** Python 3.13 on this machine has **no** `numpy`/`pytest`; the project's stack lives in the **system** Python 3.14 (`numpy 2.5.1`, `scikit-learn 1.9.1`, rasterio/shapely/scipy/pyshp present). `HANDOFF.md` assumes exactly this, but nothing in the repo records it (§8).

---

## 1. Executive summary

This is an unusually serious piece of work. The evidence discipline (raw-first ingestion, per-folder manifests, SHA-256, explicit `[F]/[I]/[O]` fact/interpretation/open tagging, "every number carries its source") is better than most professional consulting deliverables, and the project repeatedly **publishes its own failures** — the GBDT extrapolation failure, the corrected M4 estimate, the re-read of the "566658" outflow figure. That self-correcting behaviour is the project's strongest asset and I want to say that plainly before listing problems.

But "complete review" means the problems get equal weight, and there are two that matter a lot:

**1. The Goal-4 prediction model does not do what its documentation says, and its headline claim is not supported by its own results file.**
- The rainfall features `R24/R72/R168` are documented as *1/3/7-day rainfall accumulations*. The helper that builds them (`roll()` in `analysis/goal4_model_v1.py:101`) actually returns a **cumulative sum from the start of the season** — verified on a synthetic input (`roll([1..10],1) → [0,1,3,6,10,…]`) and on the real data (at 2026-09-26 12:00 the "1-day" feature reads **141,420** where a real 1-day total is ~60–97 mm). The three features are ~0.997–0.9996 correlated, i.e. one feature wearing three names. Because daily rain is spread across 24 hourly slots, they also pull in *same-day* rainfall (mild future-information leakage).
- I reproduced the shipped event RMSEs **exactly** (linear 30.9 / 103.0 / 155.4 cm at +6/+24/+48 h), which proves my re-run is faithful, then swapped in correctly lagged 1/3/7-day windows: **26.6 / 108.6 / 159.5 cm**. The linear model's advantage at +24 h disappears.
- Separately, the **shipped results file itself contradicts the headline**. `goal4_model_v1_results.json` (the 5-season run) has persistence **beating** the linear formula at +6 h (30.65 vs 30.91 cm) and +24 h (101.77 vs 103.02 cm); the formula only wins at +48 h. Yet `ANALYSIS_PLAN.md:75` prints those very 5-season numbers while asserting the formula "wins every horizon", and `goal4_model_v1_findings.md`'s headline table still quotes the superseded **3-season** numbers (28.9/96.7/145.0), where it did win everywhere.

**2. The test suite provides no protection at all.** `tests/test_core.py` imports no project module. It asserts literal arithmetic (`9.23 − 1.59 == 7.64`, `100×10×0.0036 == 3.6`, `150 ≤ 248`, constants `≤` a cap). Delete every `.py` in `analysis/` and the suite still passes 5/5. It was added in response to the earlier review's recommendation and it looks like compliance without substance — the exact failure mode the project elsewhere avoids.

Neither of these destroys the project. The flood-extent work (Sentinel-1), the datum/rating-curve derivation, the attribution (12 % : 88 %), and the counterfactual policy insight all stand on their own evidence. But the Goal-4 model is the newest, most headline-grabbing deliverable, and right now it is the least trustworthy part of the repo.

**Thai summary (for sharing with collaborators).** โครงการนี้มีวินัยด้านหลักฐานสูงมากและกล้าประกาศข้อผิดพลาดของตัวเอง ถือเป็นจุดแข็งที่หาได้ยาก แต่การรีวิวพบ 2 ประเด็นใหญ่ที่ต้องแก้ก่อนใช้ผลจริง: (1) ฟีเจอร์ฝนของโมเดลทำนาย Ny.7 (เป้าหมาย 4) ถูกสร้างผิด — ฟังก์ชัน `roll()` คืนค่า *ผลรวมสะสมตั้งแต่ต้นฤดู* ไม่ใช่ฝนสะสม 1/3/7 วัน ตามที่เขียนในเอกสาร และเมื่อแก้ให้ถูก ค่าความแม่นที่ +24 ชม. ก็ไม่ดีกว่า persistence อีกต่อไป · อีกทั้งไฟล์ผลลัพธ์จริง (`goal4_model_v1_results.json`) ชี้ว่า persistence ชนะสูตรเส้นตรงที่ +6 และ +24 ชม. ซึ่งขัดกับข้อความพาดหัวในเอกสาร (2) ชุดทดสอบ `tests/test_core.py` ไม่ได้ทดสอบโค้ดจริงเลย — ลบโค้ดทั้งโปรเจกต์ก็ยังผ่าน 5/5 จึงไม่กัน regression ตามเจตนา รายละเอียดทั้งหมดอยู่ในหัวข้อ 7, 10 และ 12.

---

## 2. Scorecard

| Dimension | Score /10 | Why |
|---|:--:|---|
| Evidence protocol & provenance | **9.0** | Raw-first, manifests, SHA-256, fact/interpretation/open tagging, archived snapshots. Docked for 4 folders without manifests and 4 without hashes. |
| Hydrological method | **8.5** | Datum calibration (218 pairs, ±0.02 m), rating curve with honest ±18–20 % caveat, hourly attribution. Single-lag lumped routing is the main weakness. |
| Remote sensing (Sentinel-1) | **8.5** | Self-built geocode+calibrate, roundtrip 0 px, same-orbit change detection, honest 360–510 km² range. No terrain correction; mask definition debatable. |
| Modelling & simulation | **5.5** | Good experimental design and honest ML-failure reporting, but the shipped model has a confirmed feature-construction defect and an unsupported headline; scenarios rest on a lumped linear superposition. |
| Reproducibility / engineering | **6.0** | Portable paths in the model scripts, `requirements.txt` present, clean git. Docked for hardcoded paths, unpinned deps, no lockfile/env doc, no CI, vacuous tests, build artifacts tracked. |
| Ease of use / communication | **8.5** | Two purpose-built HTML reports, single-file self-contained, FAQ, timeline slider, explicit AI disclaimer. Docked for Thai-only, 5 MB files, no README/entry-point index for newcomers. |
| **Overall** | **7.5** | Excellent evidence and hydrology; the newest modelling layer needs correction before it is publishable. |

---

## 3. What the project actually is

A four-goal forensic investigation of the late-September 2026 flood in Mueang Nakhon Nayok, centred on the role of the Khun Dan Prakarn Chon dam (dam_id 32, RID irrigation office 9):

1. **Evidence archive** — legally/technically citable, with hashes and provenance.
2. **Causal & compliance analysis** — rain vs dam operations, vs Rule Curve / Bang Pakong basin plan.
3. **Quantified impact** — rain vs release share at Ny.7; flood extent from Sentinel-1 + DEM.
4. **Predictive model** — 6–48 h water-level forecast for Ny.7 + forecast-informed operation scenarios.

Scope, standards and the neutrality stance are documented in `README.md` and `docs/METHODS.md`; the hand-off doc is genuinely usable. This structure is coherent and the goals are answered.

---

## 4. Methodology assessment

### 4.1 Evidence protocol — strong, with two soft spots
`METHODS.md §1` mandates raw-first capture, per-folder `manifest.md` (file, time, URL, method), SHA-256, screenshots for web/social, Wayback for public statements, and `[OCR?]` tagging for anything read off an image. This is the right protocol and it is mostly honoured.

- ✅ The re-sampling audit (same API queried at two times, Δ = 0.000) is a genuinely good idea and rarely done.
- ✅ The `[F]/[I]/[O]` taxonomy is applied consistently in the findings files.
- ⚠️ The rule "every folder in `data/` must have a `manifest.md`" is **violated by 4 folders**: `03_haii_telemetry/`, `04_tmd_rainfall/`, `11_external_forecasters/`, `manual/`.
- ⚠️ **4 manifests contain no SHA-256 at all**: `05_news_media`, `07_govt_statements`, `14_floodhub`, `17_forecast_archive`. For web captures that is defensible, but the protocol says hashes are recorded; the exception should be stated rather than silent.

### 4.2 Hydrological methods — the strongest layer
- **Datum calibration** (K1): `gauge = m MSL + 1.59 ± 0.02` from 218 matched hourly pairs. Independently cross-checked against the dam telemetry's own MSL reading. This closes a real gap (gauge-only data cannot be compared with DEM) and is properly caveated.
- **Rating curve** (K5): `Q = 242·(h − 4.55)^0.66`, fit on ~235 stage–Q pairs, mid-range accuracy good, peak underestimates ~18 % (overbank + hysteresis) → honest ±20 % envelope. Good practice.
- **Attribution** (K3): hourly integral giving dam share **~12 %** during onset (26 Sep 12:00–27 Sep 12:00) and **~57 %** during ponding (27 Sep 12:00–29 Sep 00:00). This is the project's central scientific claim and it is well-supported — with the caveat that it depends on a single 12 h lag (§7.3).
- **Basin saturation** (β flips from −0.31 to +1.49 cm/mm around 19 Sep) is a clean, falsifiable way to show the watershed lost infiltration capacity. Nice.

### 4.3 Remote sensing — impressive and honest
The Sentinel-1 pipeline (`s1_process.py`, `s1_masks.py`, `s1_change_detect.py`) is built from scratch: GCP spline + Newton inversion (roundtrip 0.00 px), σ₀ from the calibration LUT, same-orbit repeat-pass change detection to cancel incidence-angle bias, and F1-calibration against GISTDA on a shared pass. The **"GISTDA saw only 8.3 km²"** investigation is the single most valuable piece of independent verification in the repo. The 360–510 km² reporting range (rather than a false-precision point value) is exactly right.

Caveats the project already states, which I endorse: no terrain correction (acceptable for a flat target), mask can include freshly flooded paddies (+~40 % vs GISTDA), and SAR is blind to water under dense canopy and to fast-rough water → the peak figure is a lower bound for *standing* water.

### 4.4 Modelling — see §7. This is where the review concentrates its criticism.

---

## 5. Data sources assessment

| Folder | Content | Verdict |
|---|---|---|
| `01_rid_khun_dan` | Dam daily reports, FB posts, gate openings, khundan-tele station HTML | Strong; the dam-site telemetry (15-min, back to 2021) is the backbone |
| `02_thaiwater` | National Water API (dam yearly, rain chunks, water level, station registry) | Strong; API has no Q and rain only for the current year |
| `03_haii_telemetry` | — | **Empty** (host unreachable). No manifest |
| `04_tmd_rainfall` | `raw_era5/` only | Thin; **no manifest** |
| `05_news_media` | Thai PBS, Matichon, Thairath | Good; **no SHA-256** |
| `06_citizen_social` | tiny.NakhonNayok album (hundreds of images) | Good; captions separate from images |
| `07_govt_statements` | TMD / MOI / governor / ONWR | Good; MOI order is a news report, not the instrument itself; **no SHA-256** |
| `08_dem_topography` | Copernicus GLO-30, 4 tiles + GISTDA ready map | Good; **DSM not DTM** — stated |
| `09_plans_standards` | Bang Pakong basin plan (3 PDFs), rule curve | Good; internal RID regulation still missing |
| `10_mitrearth_gis` | 3rd-party GIS, 400 at-risk villages | Usable; selection criteria unknown (all-rights-reserved) |
| `11_external_forecasters` | "Tee" page, ECMWF, Flood Hub screenshots | ✅ manifest added 6 Oct (top-level index; `tee_page/` owns its own) |
| `12_gistda_flood` | GISTDA per-pass shapefiles | Good |
| `13_sentinel1_copernicus` | 17 raw scenes (~21 GB) + derived grids | Best-documented set; hashes present |
| `14_floodhub` | Google Flood Hub gauge series via internal RPC | ✅ SHA-256 added 6 Oct (8 files) |
| `15_modis_terra` | MODIS/GIBS true colour + provincial imagery | Cloud-obscured during the peak — stated |
| `16_training_data` | 15-min series, 6 seasons + NASA POWER rain | Good; Ny.7 offline in 2023 |
| `17_forecast_archive` | Real-issue 5-model forecasts, 2×/day | ✅ SHA-256 added 6 Oct (6 files) |
| `18_sentinel2_copernicus` | Sentinel-2 L2A — 3 `47PQR` (correct) + 3 `47PPS` (wrong tile) | ✅ processed 6 Oct; PPS unused, deletion pending user |
| `manual/` | 20 archives + 6 `shp_` dirs — group A **live** (report maps), group B S2 zips unused | ✅ manifest added 6 Oct; only group B (~5.8 GB) redundant |

---

## 6. Assumptions register

| # | Assumption | Plausibility | Risk | Where stated |
|---|---|:--:|---|---|
| A1 | Wave lag dam→Ny.7 is a **constant 12 h** | Medium | Medium — sensitivity to 6/12/18 h was run and the direction holds, but celerity ∝ √(gy) so the lag should shrink at peak | METHODS §8, qa5 |
| A2 | **Single-valued rating curve** (no hysteresis loop) | Medium | ±18–20 % on peak Q | khundan_tele_findings K5 |
| A3 | Bankfull at Ny.7 = gauge 8.45 m (≈ Q 425) | High | Low — anchored to the observed hour flooding began | DATA_DICTIONARY |
| A4 | **Copernicus DEM = terrain** | Medium | High for volumes (DSM, ±1–2 m vertical → 5–20× area error at 0.03 % slope). Only used for macro masks — acceptable | ANALYSIS_PLAN C4 |
| A5 | Dam release is **uniform across each day** | Low | Medium — real gate operation is step-wise; hides the hourly pulse | METHODS §8 |
| A6 | Counterfactual = linear superposition + fixed lag | Low | Medium — no routing, no backwater, no floodplain storage | goal4_counterfactual_model.py header |
| A7 | M4 diversion of 40 m³/s is feasible at Tha Chang | Low | Low (M4 is a side scenario) — flagged for FOI | ANALYSIS_PLAN D2 |
| A8 | NASA POWER 2-cell rain represents basin rainfall | Medium | Medium — coarse; knowingly used only as a model feature | DATA_SOURCES |

The project states these itself. My only addition: A1+A2+A6 **compound** in the counterfactual, and the compounding is not quantified — see §7.3.

---

## 7. Models & simulations — detailed findings

### 7.1 What the model claims
`README.md:81` / `ANALYSIS_PLAN.md:75` / `goal4_model_v1_findings.md`: a 12-feature linear formula trained on 5 seasons (13,608 h) "beats ML at every horizon" and, in the findings doc, "wins at every horizon"; GBDT fails by extrapolation; the binding constraint is the absence of forecast rainfall.

### 7.2 FINDING F-01 (High) — the rainfall features are mis-constructed and mis-labelled
`goal4_model_v1.py:101`:
```python
def roll(a, n):
    c = np.concatenate([[0], np.cumsum(a)])
    return np.array([c[max(0, i - n)] for i in range(1, len(a) + 1)])
R24, R72, R168 = roll(RT + RB, 1), roll(RT + RB, 3), roll(RT + RB, 7)
```
The docstring says "n-day sum up to this morning". The function returns `cumsum` shifted by `n`, i.e. a **cumulative sum**, not a window.

Verified two ways:
- Synthetic: `roll([1,2,…,10], 1) = [0,1,3,6,10,15,21,28,36,45]` (cumulative) vs a true 1-step window `[0,1,2,3,…]`.
- Real: at 2026-09-26 12:00 the shipped "1-day rain" feature reads **141,420** (concatenated 5-year grid) / 30,485 (2026-only grid) against a true 1-day total of **~60–97 mm**.
- Collinearity: `corr(R24,R72)=0.9996`, `corr(R24,R168)=0.9966` → effectively **one** feature, not three.

Two secondary defects in the same three lines: (a) the window argument is `1/3/7` on an **hourly** grid, so even a correct window would be 1 h/3 h/7 h, not 1/3/7 days (the names `R24/R72/R168` suggest hours, the comment says days — three mutually inconsistent readings); (b) because daily rain is replicated across 24 hourly slots, the "yesterday" value actually contains **today's** rainfall for 23 of 24 hours → mild future-information leakage into a "forecast" model.

**Impact, measured.** My faithful re-implementation reproduces the shipped event RMSEs exactly (linear 30.9 / 103.0 / 155.4 cm; persistence 30.6 / 101.8 / 170.4). Replacing the rain features with correct, properly lagged 1/3/7-day windows gives:

| +h | persistence | linear (shipped) | linear (corrected rain) |
|:--:|:--:|:--:|:--:|
| 6 | 30.6 | 30.9 | **26.6** |
| 24 | **101.8** | 103.0 | 108.6 |
| 48 | 170.4 | **155.4** | 159.5 |

So the "rain" block is not a rainfall signal at all — it is a season-progress / basin-wetness proxy, and with the intended features the model is worse at +24 h than the trivial baseline.

### 7.3 FINDING F-02 (High) — the shipped results contradict the headline claim
`goal4_model_v1_results.json` (the 5-season run, i.e. the current one) vs `goal4_model_v1_findings.md` / `ANALYSIS_PLAN.md:75`:

| +h | persistence RMSE (json) | linear RMSE (json) | "wins every horizon"? |
|:--:|:--:|:--:|:--:|
| 6 | **30.65** | 30.91 | ✗ persistence wins |
| 24 | **101.77** | 103.02 | ✗ persistence wins |
| 48 | 170.37 | **155.38** | ✓ linear wins |

The findings doc's headline table quotes the superseded **3-season** numbers (28.9/96.7/145.0), where the formula did win everywhere; its round-2 table then lists only the formula's numbers, so a reader cannot see that persistence overtook it. `ANALYSIS_PLAN.md:75` is worse: it prints the current 5-season numbers *and* the claim "wins every horizon", which those numbers do not support. The defensible claim is "the linear formula beats GBDT at every horizon, and beats persistence only at +48 h". This is a documentation-vs-artifact contradiction, not a modelling failure — but it is the kind of thing that must be corrected loudly.

> ### ⚠️ CORRECTION (6 Oct 2026 — added after the fix was actually applied)
>
> Two claims in this section are now known to be **wrong**, and the correction goes here rather than into a quiet edit.
>
> 1. **§7.2, "the rain block is not a rainfall signal at all" — false.** With the corrected features in place the rain block *does* carry real signal. Zeroing the rain columns while holding every other coefficient fixed costs **+7.0 / +21.6 / +18.3 cm** of event RMSE at +6/+24/+48 h. That direct effect is *larger* than the +4.0 / +13.3 / +11.6 cm seen when refitting without rain, so it is not an artefact of coefficient redistribution. My error was arithmetic: I read a coefficient of 0.0049 as "0.005 mm per mm" when it is **0.0049 m per mm**; against 7-day rain totals near 250 mm the contribution is tens of centimetres. The corrected features are also no longer collinear — `corr(R24,R72)=0.70`, `corr(R72,R168)=0.74`, `corr(R24,R168)=0.46`, versus 0.9996 before the fix.
>
> 2. **The suggested F-02 fix ("beats GBDT everywhere, persistence only at +48 h") — also wrong.** With corrected features GBDT wins at **+48 h** (151.1 vs 159.5) and the formula *loses* to persistence at **+24 h** (108.6 vs 101.8). The defensible claim is: *best at the operationally useful short horizons (+6 h, beating both baselines), second-best at +48 h, and beaten by persistence at +24 h.* Full tables: `analysis/goal4_model_v1_findings.md`.
>
> 3. **A third defect this review missed**, found while verifying the above: the design matrix is **rank-deficient**. `ΔH1B(6h) ≡ H1B(t) − H1B(t−6)` exactly (verified: max abs difference `0.000e+00`), so 12 columns have rank 11 and the Ny.1B coefficients are not unique. Consequences: the Ny.1B block's "signal" is **not resolvable** (bootstrap SD/|c| = 0.59–0.62, versus 0.09–0.11 for rain), and the 3-arm ablation reads non-monotonically (12 < 4 < 9 — dropping Ny.1B *helps* at +24/+48 h). Separately, `TW(t)` takes the default 2.0 for **41 % of training rows but 0 % of test rows** — a train/test distribution shift in a feature that was never flagged. Diagnostics: `analysis/goal4_feature_diagnostics.py`.
>
> Net effect on the review's conclusions: F-01 was real and is fixed; F-02 was real but the *replacement* claim I proposed was also wrong, and the true picture is more equivocal than either the original doc or this review stated.

### 7.4 The GBDT failure lesson is correct and valuable
The explanation (piecewise-constant trees cannot extrapolate above the training maximum 6.2 m; test peak 7.66 m) is sound and worth publishing. Keep it.

### 7.5 Counterfactual scenarios (R1/M1/M2/M3/M4) — useful, over-precise
The design is good: capacity-enforced every day, scenarios differentiated by decision rules, sensitivity to the lag, and the honest admission that hourly gate timing cannot be evaluated with a lumped model. The M3 insight ("stopping releases across the 26–28 Sep window matters more than the depth of pre-emptive drawdown") is a real policy contribution.

Weaknesses:
- The scenario machinery is `Q_scen = Q_obs + (release_scen − release_actual)` with one fixed lag. That is a **linear reservoir with no routing**; it cannot represent backwater, floodplain storage or hysteresis, all of which are known to matter here (the project says so elsewhere).
- The R1/M1 result has a **higher peak (9.77 m) than the actual event (9.23 m)** for a "better-managed" scenario. The doc attributes the +0.5 m to the ±18 % rating envelope, but a counterfactual where better operation raises the peak is a signal that the superposition approach is being pushed past its validity. It should be reported as "no reliable peak change" rather than a number.
- Precision: results are reported to 0.01 MCM and ±1 h from a model whose own error bars are ±18–20 % and ±6 h. Report one significant figure with the envelope.
- ~~A plot-level inconsistency: `goal4_counterfactual_model.py:178` computes the M4 line by subtracting the diversion from Q *at Ny.7*, while the text (correctly) says that is physically wrong and uses a volume-budget method instead. The plotted line therefore shows a mechanism the authors have already rejected.~~ ✅ **FIXED 6 Oct (F-08)** — the rejected method is gone from both the plot and the JSON. **But the follow-on turned out worse than the plot bug (F-14):** the volume budget that replaced it still used `AREA_CHAN = 5.0` km², the very figure §7.6 congratulates `hecras_lite_channel.py` for *correcting* to 0.90 km² — and three docs quoted a "~3 ซม." peak drop that contradicted the script's own 5.18 ÷ 509 = 1.0 ซม. Corrected to the DEM stage-storage framing (channel retains ≤ 2.0 MCM; the rest passes the city); peak drop is **1.0 cm**.

### 7.6 Hydraulic "HEC-RAS-lite"
`hecras_lite_channel.py` is a sensible first-order cross-section exercise and it **corrects an earlier over-estimate** (channel storage ~2 MCM, not the 5 km² surface implied). Good. It is explicitly not a routing model; the recommendation to do real HEC-RAS 1D/2D stands.

---

## 8. Workflow & reproducibility

**Good:** git with meaningful commit messages (the log reads as a lab notebook — genuinely useful); raw/derived separation; `requirements.txt` now exists; the model scripts resolve paths via `__file__`; the S1 pipeline is scripted end-to-end; HANDOFF documents the traps.

**Problems:**
- **F-06 (Medium) Hardcoded absolute paths.** `s1_process.py:27`, `s1_change_detect.py:15`, `s1_masks.py`, `qa5_rain_drainage_counterfactual.py` all contain `Path(r"D:\theera\Documents\code\flood")`. The S1 pipeline — the project's most impressive asset — will not run anywhere else, or even if the repo moves. Only 12 of 24 scripts use `__file__`.
- **F-07 (Medium) Unpinned dependencies, no environment record.** `requirements.txt` uses `>=` only (e.g. `numpy>=2.0`). The project's own METHODS notes that numpy 2.x changed `arr.ptp()` — that is precisely the kind of breakage a lockfile prevents. There is no `pyproject.toml`, lockfile, or venv/setup instruction; HANDOFF simply asserts "python 3.14 with everything installed". I could not run the tests with the managed interpreter and had to discover the system one.
- **F-08 (Low) cwd-dependent build scripts.** `report/build_report_html.py:5` uses `ROOT = Path(".")`, so the reports only rebuild when invoked from the repo root.
- **F-09 (Low) Build artifacts tracked in git.** The two generated HTMLs (5.1 MB and 2.6 MB) are committed. Every rebuild adds a multi-MB blob to history; these are derivable from `report/build_*.py` + `report/assets/`.
- **F-10 (Nit) Foreign tool artifact.** `.zcodeignore` (a different editor's ignore file) is committed and adds noise.

---

## 9. Ease of use

**Strengths.** The dual-track output (public HTML vs technical HTML) is well-judged. The public report has summary cards, a 16-question FAQ, a time-slider over satellite frames, and a clear AI disclaimer; the technical report carries equations, coefficients, a cross-validation matrix and a reproduction guide. Both are single self-contained files with base64-embedded images, so they survive email/chat. The AI-generated disclaimer is present in both and appropriately worded.

**Friction for a newcomer:**
- Everything is Thai-only; the code comments too. Fine for the current audience, a barrier for outside review.
- No entry point. A newcomer must guess between `README.md` (35 KB of running status), `docs/HANDOFF.md` and five other docs. A one-page `INDEX` / "start here" would help.
- The public HTML is 5.1 MB — slow to open on mobile, and every image is inlined even though several are below the fold.
- No quick-start: no `make`, no `python -m analysis.run_all`, no "run this to regenerate everything".

---

## 10. Issues register (ranked)

| ID | Severity | Issue | Evidence | Fix |
|---|:--:|---|---|---|
| F-01 | **High** | Goal-4 rain features are a cumulative sum, not 1/3/7-day windows; near-collinear; leak same-day rain | §7.2 | ✅ **FIXED 6 Oct** — shared `analysis/rain_window.py` replaces `roll()` in **all three** scripts (the review found only one); re-ran and republished. ⚠️ but see the §7.3 correction: the rain block *does* carry signal (my "season-progress proxy" conclusion was an arithmetic error) |
| F-02 | **High** | Docs claim the formula "wins every horizon"; the shipped json shows persistence wins at +6/+24 h | §7.3 | ✅ **FIXED 6 Oct** — claim restated per horizon in `goal4_model_v1_findings.md`, `ANALYSIS_PLAN.md`, `README.md`, `METHODS.md`, `HANDOFF.md`, `firo_*.md` and both report builders. ⚠️ the replacement claim proposed in this review was **also wrong** — see the §7.3 correction |
| F-13 | **High** | *(found 6 Oct, not in the original register)* Design matrix is **rank-deficient**: `ΔH1B(6h) ≡ H1B(t) − H1B(t−6)` exactly (12 cols, rank 11) → Ny.1B coefficients not unique; `TW(t)` is default-2.0 for 41 % of train rows vs 0 % of test | §7.3 correction | Resolved the *interpretation* (diagnostics added); the modelling choice is documented as an open limitation rather than silently fixed — dropping the redundant column would change the published coefficients again |
| F-03 | **High** | Tests exercise no project code | §1, §10.1 | Import and test real functions |
| F-04 | Medium | 4 scripts hardcode `D:\theera\...` | §8 | ✅ **FIXED 6 Oct** — all drive-letter paths removed; paths derive from `__file__`. ⚠️ **my claim was narrower than I first stated**: a follow-up AST scan (6 Oct, while writing `START_HERE.md`) found **8 further cwd-*relative* sites** in 5 scripts that the drive-letter check could not see — `georef_corner_match.py`, `georef_fit.py`, `georef_gistda.py`, `s1_pairs_animation.py`, `s1_peak_flood_map.py`. All 8 now derive from `__file__`; `s1_peak_flood_map.py` **proven** by running from the parent dir (output byte-identical, sha `c5aaf59f…`). Caveat: the 3 `georef_*` scripts import `cv2` (opencv), which is **not** in `requirements.txt` — they are archived experiments, not on the reproduction path |
| F-05 | Medium | 4 folders lack a manifest; 4 manifests lack SHA-256 | §4.1 | ✅ **FIXED 6 Oct** — wrote manifests for `03_haii_telemetry` (empty; host unreachable — now stated, not silent), `04_tmd_rainfall`, `11_external_forecasters` (top-level index; `tee_page/` owns its own), `manual`. Added real SHA-256 to `14_floodhub` (8 files) and `17_forecast_archive` (6 files), and stated the **no-hash exception explicitly** in `05_news_media` and `07_govt_statements` — those two folders hold no files at all, only a link log, so there is nothing to hash; the protocol gap is now visible rather than silent. All 82 recorded hashes re-verified against disk (0 mismatches). `data/manual/` is gitignored but `.gitignore` now carries a `!data/manual/manifest.md` exception (written as `data/manual/*`, since git cannot re-include a file under an excluded *directory*) so the 6.1 GB of binaries stay out of git while the inventory stays in. ⚠️ Also surfaced: `S2A_..._T47PPS_...T071759.SAFE.zip` is 27 MB where its siblings are 649 MB–1.16 GB → probably a truncated download (flagged for F-12) |
| F-06 | Medium | Unpinned deps, no env record, no lockfile | §8 | Pin versions; add `pyproject.toml`; document the interpreter |
| F-07 | Medium | Counterfactual reports 0.01-MCM precision from a ±18 % lumped model; "better" scenario has a higher peak | §7.5 | ✅ **FIXED 6 Oct** — added an uncertainty envelope to `goal4_counterfactual_model.py` (rating ±18 % → ±0.85 m at peak via `dh_per_dQ`; lag ±6 h) and made the headline **"no reliable change"** (`peak_reliable_change: false` in the JSON; `abs(peak_R1 − actual) = 0.5 m < 0.85 m`). MCM volumes now quoted to 1 s.f.; the peak is no longer claimed as a reduction. Propagated to `goal4_counterfactual_model_vs_nomodel.md`, `qa5_18day_rain_drainage_counterfactual.md`, `firo_dynamic_rulecurve_proposal.md`, `docs/ANALYSIS_PLAN.md` and both report builders |
| F-08 | Low | Dead/duplicated code: `despike` called twice per year (`goal4_model_v1.py:51–57`); `post` assigned then overwritten (`s1_change_detect.py:48`); M4 plot line uses a rejected method (§7.5) | §7 | ✅ **FIXED 6 Oct** — duplicate `despike` loop collapsed (verified no-op: all three JSONs byte-identical); dead `post` load removed; the rejected Q-subtraction method deleted from both the plot and the JSON (see F-14 for the follow-on numeric fix) |
| F-09 | Low | Docs say the calibration pre-image is "19 Sep"; the file and code use 20 Sep (UTC vs local confusion) | `s1_flood_extent_findings.md:40` vs `s1_change_detect.py:47` | ✅ **FIXED 6 Oct** — settled against `data/13_sentinel1_copernicus/manifest.md`, which states "เวลาถ่าย (UTC = ไทย−7)". Acquisition stamps are UTC, **derived filenames carry Thai time**; `587D` = 19 Sep 23:08 UTC = **20 Sep 06:09 Thai**. Corrected the doc, added a time-zone note to the methods, and fixed my own inverted comment in `s1_change_detect.py` |
| F-10 | Low | Peak level quoted as 7.64 / 7.66 / 7.68 m MSL and gauge peak 9.23 / 9.27 across files; flood duration 62 vs 65 h | grep §0 | ✅ **FIXED 6 Oct** — **one root cause, verified: two telemetry feeds of the same gauge.** thaiwater hourly reads gauge 9.23 (= 7.64 MSL); khundan-tele 15-min reads 7.68 MSL (= 9.27 gauge). Over the 218 hours present in both: median difference 0.000 m, max ±0.05 m, SD 0.017 m — feed quantisation, so the canonical pair is **9.23 gauge / 7.64 MSL ±0.05**. The **62 h duration is a data gap, not a method artifact**: the thaiwater feed is missing exactly three midnight rows (27/28/29 Sep 00:00) that khundan confirms were above bankfull — so **65 h is correct**. ⚠️ REVIEW.gemini.md attributed 62 h to a rating round-trip; **that is wrong** — I measured the h→Q→h round-trip at 1.8e-15 m and it reproduces 62 h identically. Canonical values + derivation now in `DATA_DICTIONARY.md`; the 7.66 → 7.68 error and the 9.27 inside the expert report's own M-table corrected |
| F-11 | Low | Dangling reference to a non-existent `tmp_probes/` directory | `khundan_tele_findings.md:62` | ✅ **FIXED 6 Oct** — the files were already moved to `data/01_rid_khun_dan/khundan_site/stations/kh_y{2023..2026}.html`; the reference now points there |
| F-12 | Low | Build artifacts tracked; cwd-dependent builders; `.zcodeignore`; 26 leftover files in `data/manual/` (incl. the wrong 47PPS S2 tiles) | §8 | ✅ **FIXED 6 Oct** — (a) **cwd-dependence**: all three builders now derive `ROOT` from `__file__`; **proven** by running the whole pipeline from `D:\theera\Documents\code` (the *parent* dir) — all succeeded. (b) `.zcodeignore` deleted. (c) `.gitignore` cleaned (`data/manual/*` + `!data/manual/manifest.md`; added `.pytest_cache/`). (d) **build artifacts kept tracked by decision** — the two HTMLs are the deliverable, so they stay in git (rationale recorded in `.gitignore`). (e) `data/manual/` **re-characterised**: the review's "26 leftover files" = 20 top-level archives + 6 `shp_` dirs; group A is **live** (`report/report_assets.py:271` reads the shapefiles), only group B (7 S2 zips, 5.8 GB) is unused. ⚠️ My own "27 MB = truncated download" note was **wrong** — `zipfile.testzip()` is clean (95 entries, 68 jp2); it is a valid *near-empty* PPS product. **Deletion of the wrong-tile set EXECUTED 6 Oct** on the user's confirmation ("ลบได้ (ไทล์ผิด) T47PPS"): the 4 `T47PPS` zips (2.96 GB) and the 3 extracted `T47PPS` folders (2.93 GB) were moved to the **Recycle Bin** (recoverable — verified from the bin's `$I` metadata, whose stored original paths match the 7 items exactly and nothing else was touched). The 3 `T47PQR` archives + folders and all of group A are untouched. The redundant PQR zips (~2.9 GB) are still offered for removal but **not** deleted. Note: disk space is reclaimed only when the bin is emptied |
| F-14 | Medium | *(found 6 Oct, not in the original register)* M4's volume budget used a **discredited** channel area — `goal4_counterfactual_model.py:176` set `AREA_CHAN = 5.0` km² while `hecras_lite_channel.md:13` states the DEM-derived surface is 0.90 km² and that 5 km² is "เกินจริง ~5 เท่า". The script therefore printed "ลำน้ำต่ำลง ~104 ซม.", and three docs quoted a peak drop of **~3 ซม.** although the script's own divisor gives 5.18 ÷ 509 = **1.0 ซม.** | §7.5, `hecras_lite_channel.md:20`, `ANALYSIS_PLAN.md:76`, `firo_dynamic_rulecurve_proposal.md:10,22,37` | ✅ **FIXED 6 Oct** — replaced the linear "level drop" with a volume-budget framing, so peak drop is reported as **1.0 cm** (5.18 MCM ÷ 509 km²); `channel_drop_m` removed from the JSON; all five docs corrected; both reports rebuilt. ⚠️ **the stage-storage numbers used in this first fix were themselves wrong** — see **F-15**: "channel retains ≤ 2.0 MCM at +2 m / remaining 3.2 MCM passes the city" came from `hecras_lite_channel.py`, which had a unit bug. The JSON now carries `area_flood_km2` / `area_corridor_km2` / `peak_drop_m` / `corridor_drop_m` instead of `channel_retained_mcm` / `channel_exported_mcm` |
| F-15 | **High** | *(found 6 Oct, not in the original register — during the cross-section follow-up)* **Unit bug** in `hecras_lite_channel.py::cross_section()`: `ds` (metres) was divided by `lon_scale`/`lat_scale` (**km/degree**) instead of m/degree, so the cross-section intended to be 700 m wide actually spanned **99.58°E–102.81°E (~39,800 km)**; only **2 of 35** DEM samples were valid and every reported width collapsed to 1–2 cells (20.6 / 41.2 m). The narrow widths had been *rationalised* in `hecras_lite_channel.md` as a DSM artefact | `hecras_lite_channel.py::cross_section`; `hecras_lite_channel.md`; M4 budget in `goal4_counterfactual_model.py:176` | ✅ **FIXED 6 Oct** — divide by `lon_scale * 1000.0`. Corrected widths **82–412 m** @ +1 m; corridor surface **0.90 → 11.95 km²**; stage-storage @ +2 m **2.0 → 31.6 MCM**. M4 re-expressed as a volume budget (5.18 MCM ÷ 509 km² = **1.0 cm** peak drop; ÷ ~12 km² corridor = **~44 cm**); the "2.0 MCM retained / 3.2 MCM exported" figures retracted from `goal4_counterfactual_model_vs_nomodel.md`, `firo_dynamic_rulecurve_proposal.md`, `docs/ANALYSIS_PLAN.md`, `docs/DATA_DICTIONARY.md` and the expert-report builder |
| F-16 | **High** | *(found 6 Oct, not in the original register — during the cross-section follow-up)* **Wetted-perimeter bug**: `rid_cross_section_hydraulics.py::geometry()` computed `perim = width + (seg[-1] − seg[0])`, counting the water-surface width **twice** (the free surface is not a wetted boundary — standard/HEC-RAS). P 299 → 144 m, R 1.75 → 3.65 m, Q (n=0.035) 390 → 636 m³/s, and the n matching the project rating curve **0.0268 → 0.0437**. The old figure had led `rid_cross_section_findings.md` §4 to conclude "n is abnormally low → the rating curve may be too high" | `rid_cross_section_hydraulics.py::geometry`; `rid_cross_section_findings.md` §4 | ✅ **FIXED 6 Oct** — perimeter = bed length + vertical end faces. **Reverses the published conclusion**: n = 0.0437 is *normal* for a floodplain channel, so the project rating curve is **consistent** with the surveyed geometry, not too high. §4 closed; full-range rating curve + multi-year profiles in `rid_cross_section_stage_rating.md` |

### 10.1 Why F-03 matters
`tests/test_core.py` opens with "to prevent errors from later code edits". It cannot. `test_overflow_volume_integral` re-states the arithmetic of the formula rather than calling it; `test_datum_ny7` re-states the subtraction; `test_dam_capacity_cap` asserts constants are ≤ a constant; `test_forecast_alert_threshold` asserts `150 ≤ 248`. A suite that cannot fail is worse than no suite, because it is read as coverage. The correct pattern: import `rating_h`, `datum_to_msl`, the overflow integral and the alert threshold from the modules that own them, and assert *their* output.

---

## 11. Gaps

**Blocked on a human / FOI (already identified by the project):** internal RID reservoir-operation regulation; hourly gate-operation log 25–30 Sep; benchmark/datum documents for Ny.1B and Ny.7; the definition behind the +37 MCM project-graph outflow discrepancy; Google Flood Hub API key.

**Analytical gaps I would add:**
1. **No hydrodynamic model.** Everything downstream of the rating curve is a lumped linear reservoir. HEC-RAS 1D unsteady with real cross-sections and a downstream Bang Pakong boundary is the single highest-value upgrade.
2. **No bathymetry / DTM.** Copernicus is a DSM; channel capacity and flood volume therefore carry large, unquantified uncertainty.
3. **Lag is a constant.** A first-order estimate of celerity variation across the flood would let the attribution (12 % : 88 %) carry an error bar; right now it is a point estimate.
4. **Ny.1B Q = 668.6 m³/s anomaly** (vs ~53 m³/s mean release that day) is still `[I]`. It is a large discrepancy sitting under the attribution; worth resolving or explicitly bounding.
5. **No CI and no data-integrity test.** A nightly job that re-hashes `data/` and re-runs `s1_change_detect.py` would catch silent drift.
6. **Peak extent reported inconsistently.** Fix the canonical statement: "peak 27 Sep 18:28 = 509 km² by our definition; ~360 km² under the GISTDA definition; range 360–510 km²".

---

## 12. Recommendations (prioritised)

**Do now (hours):**
1. ✅ **DONE 6 Oct.** Fix F-01: rewrite `roll()` as a true lagged window (`R1d/R3d/R7d` in days), re-run `goal4_model_v1.py`, republish the RMSE table, and update every document and both HTML reports that quote the 12-feature formula. *(Scope was larger than the review stated: the same `roll()` bug existed in `goal4_model_rainfcst_test.py` and `goal4_model_moisture_test.py` too — all three now share `analysis/rain_window.py`.)*
2. ✅ **DONE 6 Oct.** Fix F-02: restate the model's claim against the correct baseline. ~~Lead with "beats GBDT at all horizons; beats persistence only at +48 h"~~ — **that replacement was itself wrong**; the published claim is now per-horizon (best at +6 h, beaten by persistence at +24 h, beaten by GBDT at +48 h).
3. Fix F-03: make `tests/test_core.py` import the real functions. Keep it small but real.
4. Canonicalise the disputed numbers (F-10) and state the time zone for satellite pre-images (F-09).

**Added 6 Oct (from the F-01 re-verification):**
4b. Decide what to do about the rank-deficient design matrix (F-13): either drop the redundant `ΔH1B(6h)` column and republish the coefficients, or keep it and state plainly that Ny.1B coefficients are not interpretable. Also flag the `TW(t)` train/test default-rate shift (41 % vs 0 %) wherever the formula is published.
4c. Add the missing per-script reproduction entries for `goal4_model_moisture_test.py` and `goal4_feature_diagnostics.py` to the expert report's appendix (the former was never listed).

**Do soon (days):**
5. De-hardcode paths (F-04); pin dependencies and add a `pyproject.toml` + short env doc (F-06).
6. Add manifests to the 4 folders and hash notes to the 4 manifests (F-05).
7. ✅ **DONE 6 Oct.** `START_HERE.md` added — canonical reading order, the exact commands for each headline figure, split into **§4.A (reproducible from a bare clone)** vs **§4.B (needs the on-disk raw S1)**, plus a sanity-check table of the canonical numbers and the gotchas list. Written while fixing F-04's follow-up: the AST scan it prompted found 8 more cwd-relative path sites (see the F-04 register entry).
8. ✅ **DONE 6 Oct (F-12).** `.zcodeignore` removed; all three builders made cwd-independent (proven by running from the parent dir); `.gitignore` cleaned. The HTMLs are **deliberately kept** tracked — they are the deliverable. `data/manual/` re-characterised: only 4 `T47PPS` + 3 duplicate `T47PQR` S2 archives (~8.5 GB) are redundant; **deletion left to the user** (own download), proposal written into `data/manual/manifest.md`.

**Do next (weeks):**
9. HEC-RAS 1D unsteady with real cross-sections; replace the lumped scenario engine.
10. Attach uncertainty to the 12 % : 88 % attribution (lag sensitivity + rating envelope propagation).
11. Dynamic rule-curve / FIRO proposal to ONWR–RID, built on the (now corrected) M3 insight.
12. Consider a conference paper on the two genuinely novel bits: the satellite false-negative proof, and the "extreme events break tree ensembles" lesson.

---

## 13. Relationship to `REVIEW.gemini.md`

`REVIEW.gemini.md` is a thorough earlier review and much of it is fair. Two things to keep in mind when reading it alongside this one:

- **It states a number the project does not contain.** §2.2.4 says the rating curve was fit on "356 pairs"; the project's own `khundan_tele_findings.md` K5 says **235 hours**, and no project file contains "356". Treat that figure as unverified.
- **It does not surface F-01 or F-02.** It repeats the "linear wins at every horizon" claim and the "12-feature model" description without checking the feature-construction code or the results json. It also credits the test suite ("5 passed") as a strength, whereas the suite tests nothing (F-03). A review that agrees with the artefact it is reviewing is not doing the job; the whole point is to re-run the numbers.

This review is not a replacement — the Gemini review's coverage of narrative, communication design and the policy framing is broader than mine. Read both, but trust the numbers only after re-running them.

---

## 14. Appendix A — verification log

```
# tests (they pass, and that is the problem)
python -m pytest tests/ -q                     -> 5 passed in 0.01s   (tests import no project code)

# roll() semantics
roll([1..10], 1) = [0,1,3,6,10,15,21,28,36,45]        # cumulative sum, not a 1-day window
true 1-step window  = [0,1,2,3,4,5,6,7,8,9]

# real-data magnitude at 2026-09-26 12:00 (2026 grid)
shipped R24 = 30,484.6   R72 = 30,291.0   R168 = 29,903.9
true    1d  = 96.8 mm    3d  = 290.4 mm   7d  = 677.5 mm
corr(R24,R72)=0.9996  corr(R24,R168)=0.9966

# model re-run (reproduces shipped json exactly)
SHIPPED features : +6h linear 30.9 | +24h 103.0 | +48h 155.4   (persistence 30.6 / 101.8 / 170.4)
CORRECTED rain   : +6h linear 26.6 | +24h 108.6 | +48h 159.5

# repo hygiene
git status --short                             -> clean
git ls-files | wc -l                           -> 984
manifests missing                              -> 03_haii_telemetry, 04_tmd_rainfall, 11_external_forecasters, manual
manifests without SHA-256                      -> 05_news_media, 07_govt_statements, 14_floodhub, 17_forecast_archive
hardcoded D:\theera path in                    -> s1_process.py, s1_change_detect.py, s1_masks.py, qa5_rain_drainage_counterfactual.py
packaging files present                        -> requirements.txt only (unpinned); no pyproject/lock
tracked build artifacts                        -> report/*.html (5.1 MB, 2.6 MB)
```

## 15. Appendix B — minimal reproduction of F-01

```python
import numpy as np
def roll(a, n):                       # copied verbatim from analysis/goal4_model_v1.py
    c = np.concatenate([[0], np.cumsum(a)])
    return np.array([c[max(0, i - n)] for i in range(1, len(a) + 1)])

print(roll(np.arange(1, 11.), 1))     # [0. 1. 3. 6. 10. 15. 21. 28. 36. 45.]  <- cumulative
# a correct "sum of the previous n steps" is c[k] - c[max(0, k-n)]:
def window(a, n):
    c = np.concatenate([[0], np.cumsum(a)])
    return np.array([c[k] - c[max(0, k - n)] for k in range(len(a))])
print(window(np.arange(1, 11.), 1))   # [0. 1. 2. 3. 4. 5. 6. 7. 8. 9.]
```

---

## 16. Follow-up: ขยายเป็น "ทุกจุดวัด" (6 ต.ค. 69) — และข้อผิดพลาดของรีวิวนี้เอง

หลังรีวิวเสร็จ ได้ทำ P0–P3 ของ `analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md` (ดูไฟล์นั้น)
**ระหว่างทำพบว่าข้อความในรีวิวนี้เอง 3 จุดไม่ถูกต้อง — แก้แล้วใน `analysis/all_stations_plan_review.md`:**

| จุด | เดิมเขียน | ที่ถูก |
|---|---|---|
| §2.1 | "max drop/ชม." = 0.56/0.39/0.32 | **ผิดหน่วย** — นั่นคือ max **15 นาที** · ค่าต่อชั่วโมงจริง = 1.39/0.71/…/0.87 |
| §2.2 | "ฝนไม่มีเลยในทุกจุดที่สุ่ม" | **ผิด** — ฝนมีที่ 61 (11.2%), 62 (10.3%), 63 (11.3%), 84 (0.2%) |
| §2.3 | "NY.3 = 485 แถว / step 5.83 ม." | **ไม่มีหลักฐาน** — ต้นทางเป็นข้อมูลสด: ให้ 2,785 แถวช่วงหนึ่ง และ 0 แถวอีกช่วง → "ไม่แน่นอน" |

**บทเรียน:** ทั้งสามข้อเกิดจาก **สรุปจากตัวอย่างเล็กเกินไป** (แถวเดียวต่อสถานี / คอลัมน์เดียว / ตัวเลขที่ไม่บันทึกที่มา)
= ความผิดชนิดเดียวกับที่รีวิวนี้ตำหนิแผนของ AI อีกตัว (§3 Reproducibility) — ต้องบันทึกที่มาเสมอ

**ค้นพบใหม่ที่สำคัญ (มีหลักฐานดิบ + แฮชแล้ว):**
1. **datum/calibration เปลี่ยนกลางเดือน 9 จุด** (16–21, 26, 30, 84) — เช่น st16 09-16: 1.18→13.83 ·
   st26 09-17: 12.32→1.29 → **ห้ามเทียบ baseline–พีคข้ามรอยนี้** (`analysis/all_stations_network.md`)
2. **ต้นทางเปลี่ยนได้** (n_id=105) → ต้องดึงซ้ำก่อนใช้ (`data/20_multistation_levels/manifest.md`)
3. **ท่าช้าง (ท้าย ปตร.) ทำนายจาก Ny.7 ไม่ได้** — r ดิบ 0.96 เป็นเทรนด์ฤดูร่วม (ตัดเทรนด์เหลือ 0.27)
   · ตัวทำนาย "ย้ายระดับ" **แพ้ persistence 4 เท่า** · P3 เคยรายงานว่า "persistence + ΔNy.7" ดีกว่า persistence 27%
   ที่ +13 ชม. (`analysis/thachang_leadtime.md`) — **แต่พอทดสอบหลายฤดู (ฝึก 2024+2025, ทดสอบ มิ.ย.–ต.ค. 69)
   สัมประสิทธิ์ ΔNy.7 ยุบจาก 0.173 → 0.002** ⇒ B ≡ persistence · ส่วนที่ model C ดีขึ้นมาจาก **ตัวหน่วง (~0.96·y)
   + เทอม Ny.1B เล็ก** ไม่ใช่ Ny.7 (`analysis/goal4_thachang_model.md`)
   → **ข้อสรุป "ท่าช้างทำนายได้" ถูกถอน** · คำอธิบายเชิงกายภาพ: ท่าช้างอยู่ **ท้าย ปตร.** ระดับถูกกำหนดโดยบาน
   (เหมือนคลองสายใหญ่ 16–21) ไม่ใช่การไหลที่ไหลลงมาจาก Ny.7

**ข้อสรุปที่ยืนได้หลัง P0–P4:** ขยายขอบเขตจาก Ny.7 → 19 จุด **สำเร็จในเชิงข้อมูล** (16/19 มีข้อมูล, มีแฮชครบ)
แต่ **ยังไม่มีจุดที่ผ่านเกณฑ์ "มีตัวขับนำหน้า"** — 23/28/105 นำหน้า Ny.7 แต่ขับด้วยฝนร่วม ไม่ใช่ routing
และท่าช้าง/คลองสายใหญ่ ขับด้วยบาน → **เป้าถัดไปไม่ใช่ "โมเดลใหม่" แต่คือ "FOI ตารางบาน"**

**ไฟล์ใหม่ที่ P0–P4 เพิ่ม (ทั้งหมดมี manifest/แฮชหรือ input ชี้ที่มา):**
- `analysis/fetch_multistation_levels.py` · `data/20_multistation_levels/` (19 CSV + `_hashes.txt` + `manifest.md`)
- `analysis/all_stations_network.py/.json/.md` · `analysis/all_stations_goals.md`
- `analysis/thachang_leadtime.py/.json/.md` · `analysis/goal4_thachang_model.py/.json/.md`
- `analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md` · `analysis/all_stations_plan_review.md`

---

*End of review. Every finding above is reproducible from the repository at commit `5a7ced8`; where I could not verify something I have said so rather than asserting it. §16 was added 6 Oct 69 and explicitly retracts three of this review's own claims; the ThaChang claim in item 3 was additionally retracted by the multi-season test (P4).*
