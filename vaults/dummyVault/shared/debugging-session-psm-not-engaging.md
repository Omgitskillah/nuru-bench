---
id: 01M2X9KVNFXH4SSR28S893CFKA
version: 0.1.0
type: session
created: 2026-09-19T18:57
author: both
supersedes:
session: 2026-09-18-02
tags:
  - session
  - session
  - debugging
  - modem
  - analysis-test
aliases:
  - Debugging Session - PSM Not Engaging
  - 01M2X9KVNFXH4SSR28S893CFKA
---

# Debugging Session - PSM Not Engaging

# Debugging Session: PSM Not Engaging

## Goal
Get the SARA-R5 to enter Power Saving Mode and stay there.

## Timeline of AT commands (abridged, formatted badly on purpose)
```
AT+CPSMS=1,,,"00100001","00011110"
OK
AT+CPSMS?
+CPSMS: 1,,,"00100001","00011110"
OK
AT+CEREG=4
OK
+CEREG: 1,"1A2B","00C3D401",7,,,"00011110","00100001"   <-- hmm, network says T3324=00011110? but wait
AT+UPSV?
+UPSV: 0
```
Note: UPSV was 0 (power saving disabled at the UART level). PSM needs the UART/DTR side to allow deep sleep or the module never actually sleeps even if the network agreed to PSM. So there might be TWO separate problems:
1. Network-side agreement (T3324 negotiated)
2. Module-side (UPSV / DTR / RTS behavior)

## Hypothesis table
| # | Hypothesis | Evidence for | Evidence against | Status |
|---|-----------|--------------|------------------|--------|
| H1 | Network overrides T3324 | Got 10 s not 60 s | Doesn't explain no sleep at all | Confirmed (partial) |
| H2 | UPSV=0 blocks sleep | Current draw stays ~12 mA | None yet | Testing |
| H3 | Firmware keeps UART active | Logger task prints every 1 s | Would only matter with UPSV=1/2 | Plausible |
| H4 | Hardware: RTS floating | Scope shows RTS at ~1.4 V | Might be probe loading | Unverified |

## Expected current after fix
- Deep sleep (PSM): ~3 µA
- Idle connected (eDRX): ~1.2 mA avg
- Current observed: ~12 mA. If H2 fixes this that's a 4000x improvement in sleep current. Which is suspiciously good.

## Follow-up
- Try AT+UPSV=1,1280 or AT+UPSV=4 depending on R5 firmware version (check with ATI9)
- Tie DTR to a GPIO and drive it deliberately
- Stop the logger from printing while idle

## Meta
Session ran 2h40m. Consumed 3 coffees, 1 pretzel, and one (1) rubber duck.