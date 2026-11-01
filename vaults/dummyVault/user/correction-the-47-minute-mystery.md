---
id: 01M2X9K4QR8ETZ3MWKG7F3TWQE
version: 0.1.0
type: correction
created: 2026-09-19T18:57
author: user
supersedes:
targets:
  - 01M2NT6HP8THJKVENCBHBQBN5W
  - 01M2NT7XE8BF9TGFQ36A2FM2M5
tags:
  - correction
  - correction
aliases:
  - Correction - The 47 Minute Mystery
  - 01M2X9K4QR8ETZ3MWKG7F3TWQE
---

# Correction - The 47 Minute Mystery

# Correction: The 47 Minute Mystery

Earlier notes speculate that the ~47 minute PDP context drop might be a keepalive off-by-one in my firmware.

**That is wrong.** Operator support confirmed on 2026-09-18 that the NAT idle timeout on the M2M APN is roughly 45–50 min. The 47 min is a network behavior, not a firmware bug.

## What changes
- Remove "my keepalive is off by one somewhere" from the hypotheses list
- Keepalive target: 600 s (not 30 s). Safe margin = 2820 / 600 = 4.7x
- Power budget in the Area Monitor note assumed 30 s keepalive as a candidate. Ignore that line.

## What does NOT change
- PSM is still not engaging (network overrides T3324 to 10 s)
- Battery life estimates are still inconsistent between the always-connected and periodic-attach models