---
id: 01M2NT6HP8THJKVENCBHBQBN5W
version: 0.1.0
type: project
created: 2026-09-16T21:13
author: both
supersedes:
tags:
  - project
  - sample
  - project
  - embedded
aliases:
  - Area Monitor Device Redesign
  - 01M2NT6HP8THJKVENCBHBQBN5W
---

# Area Monitor Device Redesign

## Objective
Redesign the cellular communication stack for improved reliability

## Key Components
- u-blox SARA-R5 modem
- FreeRTOS kernel
- MQTT-over-TLS protocol

## Status
In Progress

## Timeline
- Phase 1: Requirements - Complete
- Phase 2: Development - 60% complete
- Phase 3: Testing - Not started



## Brain dump (unsorted, 2am edition)
- SARA-R5 keeps dropping PDP context after ~47 min idle. NOT 45, NOT 50. It's 47. Logged 9 runs: 46.8, 47.1, 47.0, 46.9, 47.2, 47.0, 47.3, 46.7, 47.0 min. mean ≈ 47.0, σ ≈ 0.19. Suspicious. Operator NAT timeout? Or my keepalive is off by one somewhere
- MQTT keepalive currently 60s. If NAT timeout is T_nat then need keepalive < T_nat/2 to be safe. Try 30s. Cost: power. See power budget below
- TODO(clarence): ask Dana whether the eSIM profile has a different APN than the bench SIM. probably does. probably why nothing works on Tuesdays

## Power budget (rough, DO NOT TRUST)
| State                   | Current (mA) | Duty (%) | Contribution (mA) |
| ----------------------- | ------------ | -------- | ----------------- |
| Modem TX burst          | 220          | 0.8      | 1.76              |
| Modem RX/idle-connected | 12           | 14       | 1.68              |
| PSM (deep sleep)        | 0.003        | 85.2     | 0.0026            |
| MCU active              | 38           | 5        | 1.90              |
| couMCU sleep            | 0.004        | 95       | 0.0038            |

I_avg ≈ 1.76 + 1.68 + 0.0026 + 1.90 + 0.0038 ≈ 5.35 mA  (hmm, that's wrong, the duty cycles for modem and MCU overlap. Recompute later)

Battery: 2 x 3.6V 19 Ah Li-SOCl2 → 38 Ah usable ~ 80% = 30.4 Ah
Life = 30.4 Ah / 5.35 mA = 5682 h = 236.8 days. Need 3 years. NOT GOOD. Unless PSM actually works. It does not work. See Tuesdays.

## Open questions
1. Is T3324 (active timer) being honored? Network gave me 0 last time, wanted 60s
2. Do we retry CONNACK timeouts with exponential backoff? Currently fixed 5s. Probably bad. Retry storm risk with 10k devices: 10000 / 5s = 2000 conn/s at broker. Broker will cry
3. Why does the watchdog fire only when I'm not looking

## Risks
- R1: Field failure rate unknown (est 2-8%, based on vibes)
- R2: Supplier lead time for SARA-R510S: 26 weeks, was 14
- R3: Certification (GCF/PTCRB) re-test if we touch the RF path. Do not touch the RF path.

## Phase 3 Testing update
Was "Not started". Now "Started, but only accidentally". Ran the soak test on the wrong firmware image (v0.9.3-dirty). Results still kind of useful.