# Mobil Uygulama — Gerçek Veri Doğrulaması (tur3)

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | USB (yan)      | dinlenme         |      10 |           2.39 |             81.3  |        14.67 |
| MCD      | USB (yan)      | egzersiz sonrası |      10 |           2.2  |             86.5  |        20.73 |
| MCD      | telefon        | dinlenme         |      10 |           2.65 |             87.45 |        12.38 |
| MCD      | telefon        | egzersiz sonrası |      10 |           2.12 |             93.8  |         8.3  |
| MCD      | webcam (önden) | dinlenme         |      10 |           9.56 |             58.96 |         4.49 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |           2    |             93    |         8.29 |

**Genel:** uygulama MAE 4.17 BPM, pencerelerin %82'i ≤5 BPM; aynı kesitlerde Python hattı MAE 11.10 BPM (60 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |   model_ms |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|-----------:|
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.27 |             96    |         0.58 |          77.5  |        433 |
| MCD      | 1020_USBVideo_after      | USB (yan)      | egzersiz sonrası |         6 |           4.46 |             50    |        10.09 |          77.5  |       2495 |
| MCD      | 1020_IriunWebcam_after   | telefon        | egzersiz sonrası |        13 |           3.08 |             76.92 |         8.49 |          77.51 |       4889 |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        18 |          37.47 |              0    |         0.73 |          75.37 |       1374 |
| MCD      | 1020_USBVideo_before     | USB (yan)      | dinlenme         |        10 |           2.32 |             80    |         4.74 |          75.37 |        494 |
| MCD      | 1020_IriunWebcam_before  | telefon        | dinlenme         |        20 |           3.54 |             80    |         1.14 |          75.37 |       2357 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         0 |         nan    |            nan    |         1.23 |          69.16 |       1719 |
| MCD      | 1024_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        22.21 |          69.16 |        nan |
| MCD      | 1024_IriunWebcam_after   | telefon        | egzersiz sonrası |         7 |           1.24 |            100    |        13.11 |          69.16 |        442 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        12 |           1.78 |            100    |         0.73 |          74.74 |       1408 |
| MCD      | 1024_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         1.18 |          74.75 |        nan |
| MCD      | 1024_IriunWebcam_before  | telefon        | dinlenme         |        18 |           2.21 |             88.89 |        18.91 |          74.75 |        439 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.52 |            100    |         0.76 |          74.39 |        493 |
| MCD      | 1035_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         3.11 |          74.38 |        nan |
| MCD      | 1035_IriunWebcam_after   | telefon        | egzersiz sonrası |        22 |           2.14 |            100    |         4.67 |          74.38 |        556 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           1.23 |            100    |         1.54 |          68.91 |        517 |
| MCD      | 1035_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         3.6  |          68.9  |        nan |
| MCD      | 1035_IriunWebcam_before  | telefon        | dinlenme         |        24 |           1.29 |            100    |         3.7  |          68.91 |        571 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.22 |             88    |         0.46 |         102.47 |        521 |
| MCD      | 1091_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           1.54 |             96    |        39.76 |         102.49 |        509 |
| MCD      | 1091_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.5  |             96    |        15.71 |         102.49 |       5555 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |         1 |          19.69 |              0    |         0.69 |          85.76 |       3027 |
| MCD      | 1091_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        19.63 |          85.76 |        nan |
| MCD      | 1091_IriunWebcam_before  | telefon        | dinlenme         |        23 |           2.46 |            100    |        10.64 |          85.76 |       2975 |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         0 |         nan    |            nan    |        17.7  |          88.71 |       3862 |
| MCD      | 1097_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         5.16 |          88.7  |        613 |
| MCD      | 1097_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |        10.33 |          88.71 |       2160 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           9.38 |             44    |        31.68 |          93.71 |        375 |
| MCD      | 1097_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        40.6  |          93.7  |        nan |
| MCD      | 1097_IriunWebcam_before  | telefon        | dinlenme         |        14 |           4.62 |             64.29 |        34.68 |          93.69 |       1072 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.45 |            100    |         1.01 |          86.37 |       2179 |
| MCD      | 1099_USBVideo_after      | USB (yan)      | egzersiz sonrası |        23 |           2.26 |            100    |        23.92 |          86.37 |       1443 |
| MCD      | 1099_IriunWebcam_after   | telefon        | egzersiz sonrası |        24 |           3.29 |             91.67 |         8.21 |          86.37 |       1482 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        22 |          11.94 |             13.64 |         1.46 |          74.33 |       1630 |
| MCD      | 1099_USBVideo_before     | USB (yan)      | dinlenme         |        23 |           2.45 |             82.61 |         9.14 |          74.36 |       2552 |
| MCD      | 1099_IriunWebcam_before  | telefon        | dinlenme         |        23 |           2.35 |             86.96 |         8.26 |          74.34 |        369 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.14 |            100    |        57.89 |         123.71 |        365 |
| MCD      | 1107_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        53.89 |         123.7  |        nan |
| MCD      | 1107_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.06 |            100    |         3.07 |         123.7  |        434 |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           2.02 |             88    |         1    |          89.41 |        337 |
| MCD      | 1107_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         7.39 |          89.42 |        nan |
| MCD      | 1107_IriunWebcam_before  | telefon        | dinlenme         |        25 |           2.09 |             92    |        24.65 |          89.4  |        365 |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           4.21 |             72    |         1.61 |          82.67 |        325 |
| MCD      | 1113_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          82.1  |        nan |
| MCD      | 1113_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         6.98 |          82.66 |        338 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           4.9  |             76    |         1.17 |          83.51 |        310 |
| MCD      | 1113_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        41.47 |          83.52 |        nan |
| MCD      | 1113_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        12.45 |          83.51 |        292 |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.71 |             88    |         1.21 |          92    |        284 |
| MCD      | 1115_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          92.04 |        nan |
| MCD      | 1115_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.54 |             92    |        11.36 |          92.02 |        285 |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           6.6  |             68    |         5.5  |          75.51 |        282 |
| MCD      | 1115_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |       nan    |          75.48 |        nan |
| MCD      | 1115_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         8.23 |          75.51 |        nan |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           0.5  |            100    |         0.4  |          67.3  |        299 |
| MCD      | 1149_USBVideo_after      | USB (yan)      | egzersiz sonrası |        21 |           0.53 |            100    |         7.71 |          67.3  |        303 |
| MCD      | 1149_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         1.02 |          67.3  |        295 |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           0.6  |            100    |         0.43 |          71.36 |        298 |
| MCD      | 1149_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         4.32 |          71.36 |       1213 |
| MCD      | 1149_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         1.19 |          71.37 |        288 |
