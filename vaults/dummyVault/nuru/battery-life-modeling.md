---
id: 01M2X9HGYHJYBM9YNQS2TAQF9Y
version: 0.1.0
type: topic
created: 2026-09-19T18:56
author: both
supersedes:
tags:
  - topic
  - embedded
  - power
  - math
  - analysis-test
aliases:
  - Battery Life Modeling
  - 01M2X9HGYHJYBM9YNQS2TAQF9Y
---

# Battery Life Modeling

# Battery Life Modeling

## Core equations
- Average current: I_avg = Σ (I_k · d_k), where d_k is the fraction of time in state k, Σ d_k = 1
- Life (hours) = (C_nominal · η_usable) / I_avg
- Peukert (for lithium primary cells it's basically ≈1, but let's pretend): t = H · (C / (I · H))^k
- Self-discharge Li-SOCl2: ~1%/year. Not negligible over 10 yr.
- Duty-cycle-weighted energy per report: E = V · (I_tx·t_tx + I_rx·t_rx + I_sleep·t_sleep)

## Measured data (Nordic PPK2, 3.6 V, 1 report/hour)
| Run | Firmware | t_attach (s) | t_tx (s) | Q_report (mC) | Notes |
|-----|----------|-------------|---------|---------------|-------|
| 1 | v0.9.1 | 4.2 | 1.1 | 612 | baseline |
| 2 | v0.9.1 | 3.9 | 1.0 | 588 | |
| 3 | v0.9.1 | 11.8 | 1.3 | 1410 | weak signal, RSRP -118 dBm |
| 4 | v0.9.2 | 4.0 | 1.0 | 601 | |
| 5 | v0.9.2 | 3.8 | 0.9 | 570 | |
| 6 | v0.9.3-dirty | 4.1 | 1.2 | 640 | wrong image, see soak test |
| 7 | v0.9.3-dirty | 0.0 | 0.0 | 0 | never attached. SIM in wrong slot. lol |

Outlier: Run 3. Do we exclude it? It's the realistic worst case, so NO. Run 7 is a mistake, YES exclude.

## Calculation attempts
Mean Q_report (runs 1,2,4,5,6) = (612+588+601+570+640)/5 = 602.2 mC
Reports/year = 24 * 365 = 8760
Charge/year = 8760 * 602.2 mC = 5275 C = 1.465 Ah
Plus sleep: 7 µA * 8760 h = 61.3 mAh
Total ≈ 1.526 Ah/yr
Life = 30.4 Ah / 1.526 Ah/yr ≈ 19.9 years?!  

...that can't be right. Earlier estimate said 237 days. One of these is wrong by a factor of ~30. (Suspect: earlier table used 14% RX duty which implies the modem is connected 24/7. This one assumes the modem is off between reports. They are different architectures. Not a math error, a *scenario* error.)

## TODO
- [ ] Reconcile always-connected vs. periodic-attach architectures
- [ ] Add temperature derating: Li-SOCl2 capacity drops hard below −20 °C
- [ ] Add passivation layer voltage delay to the model (first-pulse droop)

Related: [[Area Monitor Device Redesign]], [[FreeRTOS Task Management]]