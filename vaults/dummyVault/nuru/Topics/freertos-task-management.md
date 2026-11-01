---
id: 01M2NT6XT7KAXEJWG6R5BHNCGH
version: 0.1.0
type: topic
created: 2026-09-16T21:13
author: both
supersedes:
tags:
  - topic
  - sample
  - topic
  - embedded
  - rtos
aliases:
  - FreeRTOS Task Management
  - 01M2NT6XT7KAXEJWG6R5BHNCGH
---

# FreeRTOS Task Management

## Overview
Studying FreeRTOS task scheduling and management patterns

## Key Concepts
- Task creation and deletion
- Priority levels and preemption
- Context switching

## Resources
- FreeRTOS official documentation
- ARM Cortex-M optimization guides

## Related Projects
- Area Monitor Device Redesign



## Notes to self (messy)
- Stack sizing: I keep guessing. Use uxTaskGetStackHighWaterMark() and add 25% margin. Measured HWM (words remaining): uart_rx=112, mqtt_task=340, modem_fsm=58 (!!), logger=201, sensor_poll=96. modem_fsm is the scary one. 58 words * 4 B = 232 B headroom. one printf away from a hard fault
- Tick rate 1 kHz. configTICK_RATE_HZ=1000. Context switch cost on M4 @ 120 MHz ≈ 1.2 µs → at 1 kHz that's 0.12% overhead. fine. 
- Rate monotonic schedulability, Liu & Layland bound: U <= n(2^(1/n) - 1). For n=5 → 5*(2^0.2 - 1) = 5*0.1487 = 0.7435. My U = 0.31 + 0.08 + 0.12 + 0.05 + 0.02 = 0.58. OK under the bound. But the mutex around the UART... priority inversion!! Use priority inheritance mutex, not binary semaphore. (I used a binary semaphore. Oops. Mars Pathfinder vibes.)
- Worst-case response time: R_i = C_i + sum_{j in hp(i)} ceil(R_i / T_j) * C_j. iterate until it converges. did this by hand for modem_fsm, got 14.2 ms, deadline 20 ms. tight.

## Priority table (current)
| Task        | Priority | Period (ms) | WCET (ms) |
| ----------- | -------- | ----------- | --------- |
| uart_rx     | 5        | 10          | 0.8       |
| modem_fsm   | 4        | 50          | 6.0       |
| mqtt_task   | 3        | 100         | 12.0      |
| sensor_poll | 2        | 250         | 5.0       |
| logger      | 1        | 1000        | 20.0      |

## Idea (probably dumb)
What if the scheduler was replaced with a hand-rolled cooperative loop driven by a hardware timer capture on a spare GPIO? Deterministic! Also unmaintainable! Also I would be the only person who understands it! (This is the bad part.)

## Related
- [[Area Monitor Device Redesign]]
- [[Memfault Integration Initiative]]