# Mobil Uygulama — Gerçek Veri Doğrulaması (tur5)

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | USB (yan)      | dinlenme         |      10 |           1.97 |             88.53 |        14.67 |
| MCD      | USB (yan)      | egzersiz sonrası |      10 |           2.16 |             95.43 |        20.73 |
| MCD      | telefon        | dinlenme         |      10 |           7.84 |             56.99 |        12.38 |
| MCD      | telefon        | egzersiz sonrası |      10 |           1.76 |             95.74 |         8.3  |
| MCD      | webcam (önden) | dinlenme         |      10 |           6.18 |             68.44 |         4.49 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |           3.48 |             82.59 |         8.29 |

**Genel:** uygulama MAE 4.35 BPM, pencerelerin %79'i ≤5 BPM; aynı kesitlerde Python hattı MAE 11.10 BPM (60 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |   model_ms |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|-----------:|
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.42 |            100    |         0.58 |          77.5  |        711 |
| MCD      | 1020_USBVideo_after      | USB (yan)      | egzersiz sonrası |        14 |           3.77 |             85.71 |        10.09 |          77.5  |        646 |
| MCD      | 1020_IriunWebcam_after   | telefon        | egzersiz sonrası |         8 |           2.63 |             87.5  |         8.49 |          77.51 |       2757 |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        10 |          10.57 |              0    |         0.73 |          75.37 |       2413 |
| MCD      | 1020_USBVideo_before     | USB (yan)      | dinlenme         |        15 |           2.22 |             86.67 |         4.74 |          75.37 |       1643 |
| MCD      | 1020_IriunWebcam_before  | telefon        | dinlenme         |         9 |           5.47 |             33.33 |         1.14 |          75.37 |       2758 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         2 |           2.81 |            100    |         1.23 |          69.16 |       3362 |
| MCD      | 1024_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        22.21 |          69.16 |        nan |
| MCD      | 1024_IriunWebcam_after   | telefon        | egzersiz sonrası |        18 |           2.18 |             94.44 |        13.11 |          69.16 |        544 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        16 |           1.73 |            100    |         0.73 |          74.74 |       3428 |
| MCD      | 1024_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         1.18 |          74.75 |        nan |
| MCD      | 1024_IriunWebcam_before  | telefon        | dinlenme         |        18 |          37.45 |              5.56 |        18.91 |          74.75 |        463 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        12 |           2.87 |             75    |         0.76 |          74.39 |        459 |
| MCD      | 1035_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         3.11 |          74.38 |        nan |
| MCD      | 1035_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.02 |             96    |         4.67 |          74.38 |        615 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           1.19 |            100    |         1.54 |          68.91 |        533 |
| MCD      | 1035_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         3.6  |          68.9  |        nan |
| MCD      | 1035_IriunWebcam_before  | telefon        | dinlenme         |        25 |           1.39 |            100    |         3.7  |          68.91 |        584 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.42 |             92    |         0.46 |         102.47 |        553 |
| MCD      | 1091_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           1.6  |             96    |        39.76 |         102.49 |        520 |
| MCD      | 1091_IriunWebcam_after   | telefon        | egzersiz sonrası |         3 |           0.74 |            100    |        15.71 |         102.49 |       4721 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |         0 |         nan    |            nan    |         0.69 |          85.76 |        nan |
| MCD      | 1091_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           2    |             88    |        19.63 |          85.76 |        820 |
| MCD      | 1091_IriunWebcam_before  | telefon        | dinlenme         |         5 |           7.62 |              0    |        10.64 |          85.76 |       5211 |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         0 |         nan    |            nan    |        17.7  |          88.71 |        nan |
| MCD      | 1097_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |        10.33 |          88.71 |       2240 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           3.73 |             84    |        31.68 |          93.71 |        307 |
| MCD      | 1097_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        40.6  |          93.7  |        nan |
| MCD      | 1097_IriunWebcam_before  | telefon        | dinlenme         |        12 |           5.45 |             41.67 |        34.68 |          93.69 |        525 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        19 |          11.18 |             26.32 |         1.01 |          86.37 |       1352 |
| MCD      | 1099_USBVideo_after      | USB (yan)      | egzersiz sonrası |        21 |           2.32 |            100    |        23.92 |          86.37 |       2811 |
| MCD      | 1099_IriunWebcam_after   | telefon        | egzersiz sonrası |        23 |           1.3  |            100    |         8.21 |          86.37 |       1400 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        20 |          24.83 |              0    |         1.46 |          74.33 |       2994 |
| MCD      | 1099_USBVideo_before     | USB (yan)      | dinlenme         |        22 |           1.68 |             90.91 |         9.14 |          74.36 |       1873 |
| MCD      | 1099_IriunWebcam_before  | telefon        | dinlenme         |        24 |           2.8  |             83.33 |         8.26 |          74.34 |        309 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        20 |           2.48 |             90    |        57.89 |         123.71 |       1591 |
| MCD      | 1107_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        53.89 |         123.7  |        nan |
| MCD      | 1107_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.08 |            100    |         3.07 |         123.7  |        317 |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           2.2  |             84    |         1    |          89.41 |        768 |
| MCD      | 1107_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         7.39 |          89.42 |        nan |
| MCD      | 1107_IriunWebcam_before  | telefon        | dinlenme         |        25 |           1.95 |             92    |        24.65 |          89.4  |        330 |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           4.01 |             72    |         1.61 |          82.67 |        342 |
| MCD      | 1113_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          82.1  |        nan |
| MCD      | 1113_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         6.98 |          82.66 |        353 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           4.8  |             76    |         1.17 |          83.51 |        293 |
| MCD      | 1113_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        41.47 |          83.52 |        nan |
| MCD      | 1113_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        12.45 |          83.51 |        nan |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.58 |             88    |         1.21 |          92    |        283 |
| MCD      | 1115_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          92.04 |        nan |
| MCD      | 1115_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.75 |             88    |        11.36 |          92.02 |        284 |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           5.9  |             72    |         5.5  |          75.51 |        290 |
| MCD      | 1115_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |       nan    |          75.48 |        nan |
| MCD      | 1115_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         8.23 |          75.51 |        nan |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           0.52 |            100    |         0.4  |          67.3  |        282 |
| MCD      | 1149_USBVideo_after      | USB (yan)      | egzersiz sonrası |        21 |           0.97 |            100    |         7.71 |          67.3  |        294 |
| MCD      | 1149_IriunWebcam_after   | telefon        | egzersiz sonrası |         1 |           1.39 |            100    |         1.02 |          67.3  |        284 |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           0.64 |            100    |         0.43 |          71.36 |        287 |
| MCD      | 1149_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         4.32 |          71.36 |        300 |
| MCD      | 1149_IriunWebcam_before  | telefon        | dinlenme         |        18 |           0.59 |            100    |         1.19 |          71.37 |       1387 |
| MCD      | 1097_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         5.16 |          88.7  |       1044 |
