---
id: 01M2X9NP2R5TH9SQCB192E5KB9
version: 0.1.0
type: topic
created: 2026-09-19T18:58
author: both
supersedes:
tags:
  - topic
  - code
  - embedded
  - bug-hunt
  - analysis-test
aliases:
  - UART Ring Buffer Snippets
  - 01M2X9NP2R5TH9SQCB192E5KB9
---

# UART Ring Buffer Snippets

# UART Ring Buffer Snippets

Code review bait. There are at least two bugs in the snippet below. Model: find them.

```c
#define RB_SIZE 256

typedef struct {
    uint8_t buf[RB_SIZE];
    volatile uint16_t head;
    volatile uint16_t tail;
} ring_t;

static inline bool rb_put(ring_t *r, uint8_t b) {
    uint16_t next = (r->head + 1) % RB_SIZE;
    if (next == r->tail) return false;     // full
    r->buf[r->head] = b;
    r->head = next;
    return true;
}

static inline int rb_get(ring_t *r) {
    if (r->head == r->tail) return -1;     // empty
    uint8_t b = r->buf[r->tail];
    r->tail = (r->tail + 1) % RB_SIZE;
    return b;
}

// ISR
void USART1_IRQHandler(void) {
    uint8_t c = USART1->DR;
    rb_put(&rx_ring, c);      // ignores overflow
}
```

## Known issues (spoilers)
1. Overflow is silently dropped. No counter, no error flag
2. Returns `int` but mixes -1 sentinel with valid 0-255. OK actually, but call sites that store into uint8_t will break
3. No memory barrier on head/tail with multi-core or DMA. On a single M4 with volatile it's usually fine
4. Capacity is RB_SIZE − 1 = 255, not 256. Off-by-one in my documentation

## Throughput math
At 115200 baud 8N1: 11520 bytes/s → one byte per 86.8 µs. With RB_SIZE=256, a full buffer represents 22.2 ms of data. If the consumer task runs every 50 ms (modem_fsm period) → overflow! Buffer needs ≥ 11520 · 0.05 = 576 B minimum, so pick 1024.

At 921600 baud: 92160 B/s → 1024 B fills in 11.1 ms. Consumer must run at least every ~5 ms or use DMA with idle-line detection.

Related: [[FreeRTOS Task Management]]