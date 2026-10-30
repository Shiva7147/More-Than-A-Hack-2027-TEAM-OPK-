# Team OPK — Technical Report: Physics-Informed Controlled Possession State Machine

**Competition:** More than a Hack 2027 — Phase 1: Ball Possession  
**Organizers:** Metrica Sports, FC Barcelona, Mobile World Capital Barcelona (Talent Arena)  
**Match:** FC Barcelona (`H`) vs Athletic Club (`A`) — LaLiga EA Sports 2024–25 (Matchday 2)  
**Team Name:** **OPK**  
**Submission Artifact:** `OPK.csv` (199,319 frames)  

---

## 1. Executive Summary & Problem Formulation

In Phase 1 of *More than a Hack 2027*, the task is to predict the continuous possession label for every frame ($199,319$ frames at $25\text{ fps}$, $\sim 106$ minutes of graded play) between Home (`H` — FC Barcelona), Away (`A` — Athletic Club), Dead Ball (`D`), or Abstain (`X`).

The ranking metric is **`spellF1`**, which evaluates predicted continuous possession spells against ground truth spells via temporal Intersection over Union (IoU $\in [0.3, 0.7]$), with **`macroF1`** as the tie-breaker.

The official reference baseline (`baseline_smooth50`) naively assigns possession to the nearest player to the ball and applies majority voting over a sliding window. This approach suffers from three critical failure modes:
1. **The False Turnover Trap:** Passing passes near an opponent or momentary loose balls trigger immediate false possession flips, fracturing $40\text{s}$ possessions into micro-fragments and destroying `spellF1`.
2. **The 41% Missing Ball Void:** The ball is unobserved on $41\%$ of graded frames. The baseline defaults to dead ball or leaves gaps, splitting possessions.
3. **Ghost Dead-Ball Ownership:** During real stoppages (throw-in preparations, goal kicks, post-goal celebrations), the baseline predicts active player possession because players are walking near the ball.

**Team OPK's Solution:** A **Physics-Informed Controlled Possession State Machine** (`engine_opk.py`) combining physical ball-player proximity thresholds, turnover dwell-time filtering, airborne ball velocity continuity, and Smart Tagging tactical anchoring.

---

## 2. The Algorithmic Architecture

```
                                  ┌────────────────────────┐
                                  │ Raw Tactical ATD Feed  │
                                  │ (22 Players + Ball)    │
                                  └───────────┬────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
          ┌─────────────────────────┐                   ┌─────────────────────────┐
          │ Physical Feature Engine │                   │ Smart Tagging Synthesizer│
          │ • Euclidean dist d_H,d_A│                   │ • Kickoff anchors (1&2) │
          │ • Ball speed & in-flight│                   │ • Post-goal celebration │
          │ • Pitch boundary check  │                   │ • Set-piece restarts    │
          └────────────┬────────────┘                   └────────────┬────────────┘
                       │                                             │
                       └──────────────────────┬──────────────────────┘
                                              │
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │ Controlled Possession State Machine       │
                        │                                           │
                        │ • Control Radius: R_ctrl <= 2.0m          │
                        │ • Turnover Dwell: T_turn >= 18 frames     │
                        │ • Airborne Pass Continuity (v > 7.5 m/s)  │
                        │ • Missing Ball Occlusion Tolerance (<2.5s)│
                        └─────────────────────┬─────────────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │ Official Submission File  │
                                │ OPK.csv (199,319 frames)  │
                                └───────────────────────────┘
```

### Core Possession Rules Implemented:
* **The Controlled Possession Principle:** In football, proximity alone does not equal possession. Opposing players only take possession if they remain within $R_{\text{control}} \le 2.0\text{m}$ of the ball for at least $T_{\text{turnover}} = 18$ consecutive frames ($0.72\text{s}$). Deflections, contested duels, or passes that merely brush an opponent maintain possession with the original team.
* **Airborne Pass Continuity:** When ball speed exceeds $7.5\text{m/s}$ and minimum distance to any player exceeds $1.5\text{m}$, the ball is in flight. The state machine locks turnover evaluation, preventing mid-air possession flips.
* **Occlusion Tolerance Window:** When the ball tracker loses sight of the ball (41% of frames):
  * **Short Occlusions ($< 60$ frames / $2.4\text{s}$):** Possession remains locked to the possessing team (passes, crowded box scrums).
  * **Long Dropouts ($> 60$ frames):** The state machine transitions to Dead Ball (`D`).
* **Boundary & Stoppage Physics:** If ball coordinates exit normalized pitch dimensions ($x \notin [-0.015, 1.015]$, $y \notin [-0.015, 1.015]$), state immediately resets to Dead Ball (`D`).
* **Tactical Landmark Clamping:**
  * Pre-match and halftime intervals ($[0, 11185)$ and $[99000, 113742)$) are clamped to `D`.
  * The 4 post-goal celebration intervals identified in Smart Tagging are clamped to `D` up to the referee's restart kickoff.

---

## 3. Data Assets Used

| Asset | Role in Team OPK Pipeline | Usage Status |
|---|---|---|
| `BAR-ATH_tactical_atd.txt` | Primary tracking feed: 22 player positions and ball coordinates. | **Active Core** |
| `BAR-ATH_tactical_atd.xml` | Metadata establishing team IDs (Home = Barcelona, Away = Athletic Club). | **Active Core** |
| `BAR-ATH_tactical_homography.csv` | Planar homography converting pitch to metric coordinates ($105.3\text{m} \times 68.0\text{m}$). | **Active Core** |
| `BAR-ATH_tactical_smart_tagging.xml` | 638 tactical phases: used for kickoff synchronization and celebration dead-ball clamping. | **Active Core** |
| `BAR-ATH_tactical.mp4` | Video inspection for qualitative validation. Not required during execution. | Verified / Dropped |
| `broadcast/*` | Evaluated but excluded: non-continuous timeline and replays introduce phase misalignment. | Excluded |

---

## 4. Training Data & Compliance (Rules 1, 2 & 3)

* **Zero Human Annotations on Provided Game:** No human labels, manual keypoint corrections, or semi-supervised human-in-the-loop annotations were used on the test match. All labels are generated **100% deterministically by code**.
* **Zero Private Ground Truth Leakage:** The model was designed purely from physical principles and domain rules. The public 5-minute ground truth was used solely as a sanity check to verify pipeline sanity and coordinate conventions, strictly respecting `RULES.md`.
* **100% Bit-for-Bit Deterministic Reproduction:** Running `python starter/engine_opk.py` regenerates the exact submitted `OPK.csv` in under 15 seconds.

---

## 5. Benchmark Results & Verification

Evaluated on the official public ground truth window ($7,500$ graded frames, $17$ possessions, mean duration $14.2\text{s}$):

| Submission | `macroF1` (Tie-break) | `spellF1` (Primary) | Transition F1 | Share Error | Spells Count | Mean Duration |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Team OPK (`OPK.csv`)** | **0.6658** | **0.4205** | **0.2553** | **0.033** | **22** | **12.3 s** |
| `baseline_smooth50` (Floor) | 0.6207 | 0.3256 | 0.0816 | 0.048 | 26 | 10.8 s |
| `baseline_smooth25` | 0.6200 | 0.2868 | 0.2034 | 0.056 | 36 | 7.6 s |
| `baseline_raw` | 0.5972 | 0.0378 | 0.1410 | 0.046 | 131 | 2.0 s |

### Key Findings:
1. **Superior Transition Accuracy:** Team OPK achieves a Transition F1 of **`0.2553`**, more than **3.1× higher** than `baseline_smooth50` (`0.0816`).
2. **Minimal Share Error:** Team OPK drops overall possession share error to **`3.3%`** (lowest on the board).
3. **No Fragmentation:** Mean spell duration of $12.3\text{s}$ closely matches real football dynamics ($14.2\text{s}$ ground truth) without artificial over-smoothing.

---

## 6. Limitations & Future Roadmap

* **Ultra-Crowded Box Occlusions:** When $>6$ players contest a corner kick with the ball invisible, the state machine defaults to Dead Ball after $2.4\text{s}$. A multi-player convex hull model could infer possession from team pressing centroid shifts.
* **Broadcast Synchronization:** Leveraging broadcast multi-angle homographies could provide alternative camera angles during tactical camera occlusions.

---

## 7. How to Reproduce

In the project root directory:

```bash
# 1. Install dependencies (standard numpy & pandas only)
pip install -r requirements.txt

# 2. Run the Team OPK Championship Engine (takes ~12 seconds)
python starter/engine_opk.py

# 3. Validate file format against competition contract
python evaluation/validate_submission.py evaluation/results/OPK.csv

# 4. Run official evaluation
python evaluation/run_evaluation.py
```
