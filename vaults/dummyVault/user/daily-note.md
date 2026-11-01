---
id: 01M2NT7XE8BF9TGFQ36A2FM2M5
version: 0.1.0
type: daily
created: 2026-09-16T21:14
author: user
supersedes:
date: '2026-09-16'
tags:
  - daily
  - sample
  - daily
aliases:
  - Daily Note
  - 01M2NT7XE8BF9TGFQ36A2FM2M5
---

# Daily Note

## Focus Areas
1. Complete MQTT protocol implementation
2. Debug modem connection issues
3. Review architecture feedback

## Meetings
- 10:00 - Team standup
- 14:00 - Architecture review

## Completed Tasks
- ✅ Fixed UART baud rate configuration
- ✅ Optimized task scheduling
- ✅ Updated documentation

## Blockers
- Waiting for hardware test results

## Notes
Good progress on firmware. Need to focus on error handling tomorrow.



## Later that day (added after coffee #4)
- Scope trace of UART TX at 115200 8N1: bit time should be 8.68 µs. Measured 8.71 µs. 0.35% off. Fine. Then switched to 921600 and got framing errors. 921600 bit time = 1.085 µs. HFCLK error budget: need < ~2% total. Clock divider gives 3.1%. Yeah that's the bug. Baud rate error = (actual - target)/target. Should've done this math BEFORE burning an hour.
- Lunch: forgot. Ate 3 pretzels around 15:30.
- Fun thought: a 555 timer is technically a tiny mixed-signal state machine and nobody talks about it enough. Also the LM358 is a spiritual ancestor of every regret I have about single-supply op-amp design.
- Voltage divider for battery sense: Vout = Vin * R2/(R1+R2). R1=1M, R2=330k, Vin=3.6 → Vout=0.894 V. ADC ref is 1.2 V so OK. But leakage = 3.6/1.33M = 2.7 µA. That is 2.7 µA forever. Over 3 years that's 71 mAh. Hmm. Switch it with a FET.

## Blockers (updated)
- Hardware test results STILL not back
- Dana is on vacation until the 28th
- Lab bench PSU has a bad ground clip. Do not trust its current readout. Off by ~0.4 mA at low range

## Mood: 6/10. Would be 8/10 with a working PSM.