
# LoRa Time-on-Air and Duty Cycle Compliance

This document outlines the step-by-step procedure for calculating the Time-on-Air (ToA) for our LoRa packet configuration. The parameters used are based on the official Semtech SX1276 datasheet.

## LoRa Packet Configuration Parameters

| Parameter                        | Value                        | Units     |
|----------------------------------|------------------------------|-----------|
| Spreading Factor (SF)           | 7                            | --        |
| Bandwidth (BW)                  | 125                          | kHz       |
| Payload Size (PL)               | 240                          | bytes     |
| Coding Rate (CR)                | 1 (⇒ 4/5)                    | --        |
| Cyclic Redundancy Check (CRC)   | 1 (⇒ Enabled)                | --        |
| Low Data Rate Optimization (DE) | 0 (⇒ Disabled)               | --        |
| Preamble Length (n_preamble)    | 8                            | symbols   |

## 1. Symbol Duration (T_symbol)

```
T_symbol = 2^SF / BW = 2^7 / 125000 = 1.024 ms
```

## 2. Preamble Duration (T_preamble)

```
T_preamble = (n_preamble + 4.25) × T_symbol
           = (8 + 4.25) × 1.024 = 12.544 ms
```

## 3. Payload Symbols (n_payload)

```
n_payload = 8 + max(ceil((8×PL - 4×SF + 28 + 16×CRC - 20×IH) / (4×(SF - 2×DE))) × (CR + 4), 0)

With PL = 240, SF = 7, H = 0, DE = 0, CR = 1:
n_payload = 8 + ceil(1936 / 28) × 5 = 8 + 70 × 5 = 358
```

## 4. Payload Duration (T_payload)

```
T_payload = n_payload × T_symbol = 358 × 1.024 = 366.59 ms
```

## 5. Total Packet Time-on-Air (T_packet)

```
T_packet = T_preamble + T_payload = 12.544 + 366.59 = 379.13 ms
```

## Spectrum Verification

The calculated ToA has been experimentally verified using spectrum analysis with a Software Defined Radio (SDR). A demonstration GIF file is shown below:
![SDR Demo GIF](sdr_demo.gif)

The screen capture is done at 0.1x speed, with a total time of ~9.6 seconds. Each packet occupies the spectrum for less than 400 ms, complying with the FCC 400 ms transmission time (dwell time) limit in the 915 MHz band.

## Duty Cycle Strategy

Although each transmission complies with dwell time, the current IFT implementation does not yet meet the FCC's 20-second OFF-time requirement per channel.

To address this, we propose a channel hopping scheme using frequencies from 902.5 MHz to 927.5 MHz in 0.5 MHz steps.

### Number of Channels

```
Number of channels = 2 × (927.5 - 902.5) + 1 = 51
```

### Total Cycle Time

```
Total cycle time = 51 × 400 ms = 20.4 seconds
```

This ensures that each channel remains idle for 20.4 seconds before reuse, staying within regulatory limits.

## Future Optimization

While this conservative approach ensures compliance, further optimizations are possible. These include reducing hop spacing, tuning SF/BW, and implementing adaptive strategies. These would impact efficiency, power usage, and spectral utilization, and are reserved for future work.
