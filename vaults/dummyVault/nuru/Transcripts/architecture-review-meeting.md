---
id: 01M2NT76JAEZXYFQ05WCCFAGGF
version: 0.1.0
type: transcript
created: 2026-09-16T21:13
author: both
supersedes:
session: 2026-09-14-02
tags:
  - transcript
  - sample
  - transcript
  - architecture
aliases:
  - Architecture Review Meeting
  - 01M2NT76JAEZXYFQ05WCCFAGGF
---

# Architecture Review Meeting

## Participants
- Clarence
- Architecture Review Board

## Agenda
1. Cellular modem abstraction layer design
2. Error handling and recovery strategies
3. Security considerations for TLS

## Decisions Made
- Approved the modem abstraction design
- Require circuit breaker pattern for connection recovery
- TLS certificate pinning mandatory for production

## Follow-ups
- [ ] Update design documentation
- [ ] Create security threat model



## Raw transcript fragments (unedited, speaker labels may be wrong)
**Clarence:** so the circuit breaker, right, after N failures we open it and back off, and my current N is like, three?

**ARB member 1:** Three is aggressive. What's the reset timeout?

**Clarence:** Uh. Thirty seconds. Fixed.

**ARB member 2:** Fixed is a problem. You want exponential with jitter. Something like t_n = min(t_max, t_0 * 2^n) + rand(0, t_0). Otherwise every device wakes up at the same time after a network outage and you DDoS yourself.

**Clarence:** Yeah, we have ten thousand units, so that's uh, that's a lot of synchronized reconnects.

**ARB member 1:** Try t_0 = 2 s, t_max = 900 s. After 9 failures you're at the cap: 2 * 2^9 = 1024 > 900.

**Clarence:** Cool. Also for the pinning thing, do we pin the leaf or the intermediate? Leaf rotates every 90 days.

**ARB member 2:** Pin the intermediate CA public key hash. Not the leaf. Definitely not the leaf.

**Clarence:** okay okay. Writing that down. (writes it down on wrong sticky note)

## Action items (extracted, some duplicates)
- [ ] Implement exponential backoff with jitter
- [ ] Implement exponential backoff with jitter (dupe on purpose)
- [ ] Pin intermediate CA, not leaf
- [ ] Find the sticky note
- [x] Complain about Mondays

## Off-topic aside
Someone asked if Rust would fix all of this. Answer: it would fix maybe 30% of it and create a new 30%.