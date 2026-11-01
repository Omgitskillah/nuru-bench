---
id: 01M2X9P3CRRBJFFPJ0EYXVCTRB
version: 0.1.0
type: topic
created: 2026-09-19T18:58
author: both
supersedes: 01M2X9HGYHJYBM9YNQS2TAQF9Y
tags:
  - topic
  - embedded
  - power
  - math
  - analysis-test
aliases:
  - Battery Life Modeling Revised
  - 01M2X9P3CRRBJFFPJ0EYXVCTRB
---

# Battery Life Modeling Revised

# Battery Life Modeling (Revised)

Supersedes the earlier note. Reconciles the two architectures.

## Two architectures, done properly
**A. Always-connected (eDRX, no PSM):** I_avg ≈ 5.35 mA (from earlier table, overlap not corrected). Life = 30.4 Ah / 5.35 mA = 5682 h ≈ 237 days.

**B. Periodic attach, modem fully off between reports:** ≈ 1.53 Ah/year → naive 19.9 years.

## Realistic bounds for B
- Self-discharge: 1%/yr → over 10 yr the cell loses ~10% just sitting. Reduces usable capacity: 30.4 · 0.9 ≈ 27.4 Ah at year 10
- Passivation voltage delay at cold: can brown out the modem TX burst below −20 °C → extra retries → more charge per report. Assume +40% Q_report at cold: 602 mC → 843 mC
- Assume 25% of reports need a retry (weak signal, cf. Run 3 at 1410 mC): E[Q] = 0.75·602 + 0.25·1410 = 451.5 + 352.5 = 804 mC
- Charge/year = 8760 · 0.804 C = 7043 C = 1.956 Ah, plus sleep 0.061 Ah → 2.02 Ah/yr
- Life ≈ 27.4 / 2.02 ≈ 13.6 years, capped by shelf life (~10 yr practical). So in B the battery is not the limiting factor.

## Conclusion (tentative)
Requirement of 3 years is met with margin only if the device uses periodic attach or PSM truly works. Always-connected fails by 5x.
Sensitivity: reports/hour going from 1 → 6 multiplies the active charge by 6 → Life ≈ 27.4 / (6·1.956 + 0.061) ≈ 2.3 years. Fails 3-year target. Worth showing to the manager.

## Still unknown
- Actual reporting interval the product team wants (nobody has said)
- Whether latency requirements force always-connected (alarm path!). If a gas alarm must reach the cloud in < 5 s, periodic attach may be unacceptable. This is the real tension.

Supersedes [[Battery Life Modeling]]. Related: [[Area Monitor Device Redesign]]