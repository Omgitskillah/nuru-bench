---
id: 01M2X9HVPNTE983VPKX87CPS3M
version: 0.1.0
type: topic
created: 2026-09-19T18:56
author: both
supersedes:
tags:
  - topic
  - sensors
  - data
  - analysis-test
aliases:
  - Sensor Calibration Data
  - 01M2X9HVPNTE983VPKX87CPS3M
---

# Sensor Calibration Data

# Sensor Calibration Data

Electrochemical gas sensor, bench calibration against reference gas. Temperature compensation experiment.

## Raw readings (ADC counts, 16-bit) vs. concentration (ppm)
```csv
ppm,adc_25C,adc_0C,adc_-10C,adc_40C
0,812,790,771,843
10,1490,1441,1398,1552
25,2510,2422,2351,2630
50,4205,4051,3920,4402
100,7588,7302,7069,7951
200,14102,13540,13091,14803
```

## Fit notes
- Linear fit at 25 °C: adc = a·ppm + b. Least squares gives roughly a ≈ 69.2 counts/ppm, b ≈ 900 (eyeballed, please verify)
- Residual at 200 ppm looks nonlinear. Maybe sensor saturating? Or maybe I'm just tired.
- Temperature coefficient of sensitivity at 100 ppm: (7951 − 7588)/(40−25) = 24.2 counts/°C. ≈ 0.32%/°C. Datasheet claims 0.25%/°C. So either my sensor is bad or the datasheet is optimistic. (It's the datasheet. It's always the datasheet.)
- Zero drift: (843−812)/15 = 2.07 counts/°C

## Compensation formula (draft)
ppm_corrected = (adc_raw − Z(T)) / S(T)
Z(T) = Z25 + kz·(T − 25)
S(T) = S25 · (1 + ks·(T − 25))
with kz ≈ 2.07 counts/°C, ks ≈ 0.0032 /°C

## Gotchas
- Sensor needs ~90 s warm-up. First 3 readings are garbage. Discard.
- Humidity cross-sensitivity untested. Nobody has a humidity chamber. I looked into building one from a Tupperware container and a humidifier. This was a mistake.
- One reading in the set is a deliberate outlier: (50 ppm, 0 °C) probably fine, but (100 ppm, −10 °C) seems low. Might be a transcription error.

Related: [[Area Monitor Device Redesign]]