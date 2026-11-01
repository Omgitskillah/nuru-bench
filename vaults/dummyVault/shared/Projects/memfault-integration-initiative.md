---
id: 01M2NT6ME093S3SSSD39CDVCPE
version: 0.1.0
type: project
created: 2026-09-16T21:13
author: both
supersedes:
tags:
  - project
  - sample
  - project
  - monitoring
aliases:
  - Memfault Integration Initiative
  - 01M2NT6ME093S3SSSD39CDVCPE
---

# Memfault Integration Initiative

## Objective
Integrate Memfault diagnostics for remote device monitoring

## Key Components
- Coredump capture and storage
- Metrics collection
- OTA update support

## Status
Planning

## Timeline
- Phase 1: Architecture design - 30% complete
- Phase 2: SDK integration - Not started
- Phase 3: Testing and validation - Not started



## Sizing math (napkin, subject to being wrong)
Flash budget for coredumps: PSoC 6 external flash sector = 4 KB erase unit. Coredump = registers (~0.5 KB) + stack snapshot + selected RAM regions.
- Minimal coredump: 0.5 KB regs + 4 KB stack + 8 KB heap metadata ≈ 12.5 KB → rounds up to 16 KB (4 sectors)
- Full RAM dump: 288 KB (SRAM). Does not fit alongside OTA slot. Nope.
- Wear: NOR flash ~100k erase cycles/sector. If a crash-looping device writes a coredump every 30 s: 4 sectors * 1 erase per 30 s → each sector erased 2880 times/day → 100000 / 2880 ≈ 34.7 days to death. NEED rate limiting. Suggest max 1 dump per hour → 24 erases/day/sector → 11.4 years. OK.

Metrics upload budget: 40 metrics * 4 B = 160 B + chunk overhead ~15% ≈ 184 B per heartbeat. Hourly heartbeat over cellular: 184 B * 24 = 4.4 KB/day = 132 KB/month. Data plan is 500 KB/month total. So Memfault eats 26%. Hmm. Try 3-hour heartbeat: ~44 KB/month = 9%.

## Status log (chronological-ish)
- 09-08: Read docs. Docs are good. My understanding of docs is bad.
- 09-10: Got the SDK to compile. Linker script fight (.noinit region collides with our bootloader shared-RAM block at 0x08000000+). Moved it.
- 09-12: First fake crash via `memfault_assert`. Coredump visible in the portal. Felt like a wizard for 4 minutes.
- 09-15: Realized the device serial numbers are not unique on the prototype batch (dupes: 0x1A2B, 0x1A2B, 0x1A2C). Memfault will merge them into one device. Fix in provisioning script.

## Decision pending
Send data over MQTT (reuse existing pipe, 1 broker to maintain) or Memfault's HTTPS chunk endpoint (their recommended path, extra TLS handshake ~6 KB overhead each time)? Leaning MQTT. Security review may disagree.

## Status
Actually "Started" not "Planning". Phase 2 is ~15% done, please update the earlier section.