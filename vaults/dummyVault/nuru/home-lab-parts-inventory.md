---
id: 01M2X9MPNE5K167B6F059NJS8X
version: 0.1.0
type: topic
created: 2026-09-19T18:57
author: user
supersedes:
tags:
  - topic
  - inventory
  - data
  - hobby
  - analysis-test
aliases:
  - Home Lab Parts Inventory
  - 01M2X9MPNE5K167B6F059NJS8X
---

# Home Lab Parts Inventory

# Home Lab Parts Inventory

| Part | Qty | Unit cost (EUR) | Bin | Notes |
|------|-----|-----------------|-----|-------|
| 10k 1% 0603 resistor | 480 | 0.004 | A1 | plenty |
| 100 nF X7R 0603 | 350 | 0.006 | A2 | |
| 1 MΩ 1% 0603 | 12 | 0.005 | A1 | need more, see battery sense |
| 330 kΩ 1% 0603 | 9 | 0.005 | A1 | |
| LM358 DIP-8 | 6 | 0.35 | B3 | spiritual ancestor |
| NE555 DIP-8 | 14 | 0.28 | B3 | |
| STM32F103 bluepill | 3 | 4.20 | C1 | one is dead, unknown which |
| nRF52840 dongle | 2 | 10.50 | C1 | |
| u-blox SARA-R510S EVK | 1 | 189.00 | D | borrowed from work, do not lose |
| 2N3904 | 40 | 0.03 | B1 | for the discrete adder |
| 1N4148 | 100 | 0.01 | B1 | |
| Nylon M3 standoff 10 mm | 0 | 0.08 | E | OUT. Need to order. |

## Quick math
Total inventory value ≈ Σ qty × cost
= 480·0.004 + 350·0.006 + 12·0.005 + 9·0.005 + 6·0.35 + 14·0.28 + 3·4.20 + 2·10.50 + 1·189 + 40·0.03 + 100·0.01 + 0
= 1.92 + 2.10 + 0.06 + 0.045 + 2.10 + 3.92 + 12.60 + 21.00 + 189.00 + 1.20 + 1.00 + 0
≈ 234.95 EUR (of which 189 EUR is not even mine)

## Reorder list
- 1 MΩ 1% 0603 ×100
- Nylon standoffs ×50
- 1 F supercap, low ESR (only if Alice wins)