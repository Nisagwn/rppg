# Mobil Uygulama — Gerçek Veri Doğrulaması (7E)

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | USB (yan)      | dinlenme         |      10 |           1.86 |             92.82 |        14.67 |
| MCD      | USB (yan)      | egzersiz sonrası |      10 |           4.15 |             73    |        20.73 |
| MCD      | telefon        | dinlenme         |      10 |           6.45 |             76.14 |        12.38 |
| MCD      | telefon        | egzersiz sonrası |      10 |           2.18 |             92.08 |         8.3  |
| MCD      | webcam (önden) | dinlenme         |      10 |           6.13 |             76.26 |         4.49 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |           2    |             92.96 |         8.29 |

**Genel:** uygulama MAE 3.98 BPM, pencerelerin %84'i ≤5 BPM; aynı kesitlerde Python hattı MAE 11.10 BPM (60 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |   model_ms |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|-----------:|
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        18 |           4.86 |             72.22 |         0.58 |          77.5  |       1408 |
| MCD      | 1020_USBVideo_after      | USB (yan)      | egzersiz sonrası |        13 |           8.03 |             30.77 |        10.09 |          77.5  |       2350 |
| MCD      | 1020_IriunWebcam_after   | telefon        | egzersiz sonrası |        14 |           3.03 |             71.43 |         8.49 |          77.51 |       1799 |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        16 |           4.02 |             68.75 |         0.73 |          75.37 |       1235 |
| MCD      | 1020_USBVideo_before     | USB (yan)      | dinlenme         |        22 |           1.87 |             90.91 |         4.74 |          75.37 |        858 |
| MCD      | 1020_IriunWebcam_before  | telefon        | dinlenme         |         2 |           0.58 |            100    |         1.14 |          75.37 |        888 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        21 |           1.52 |            100    |         1.23 |          69.16 |        409 |
| MCD      | 1024_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        22.21 |          69.16 |        nan |
| MCD      | 1024_IriunWebcam_after   | telefon        | egzersiz sonrası |        14 |           2.18 |             92.86 |        13.11 |          69.16 |        234 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        19 |           1.6  |            100    |         0.73 |          74.74 |        234 |
| MCD      | 1024_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         1.18 |          74.75 |        nan |
| MCD      | 1024_IriunWebcam_before  | telefon        | dinlenme         |        17 |           2.39 |             88.24 |        18.91 |          74.75 |        279 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        23 |           2    |             91.3  |         0.76 |          74.39 |       1228 |
| MCD      | 1035_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         3.11 |          74.38 |        nan |
| MCD      | 1035_IriunWebcam_after   | telefon        | egzersiz sonrası |        18 |           1.74 |            100    |         4.67 |          74.38 |        251 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           1.14 |            100    |         1.54 |          68.91 |        641 |
| MCD      | 1035_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         3.6  |          68.9  |        nan |
| MCD      | 1035_IriunWebcam_before  | telefon        | dinlenme         |        25 |           0.85 |            100    |         3.7  |          68.91 |        835 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.33 |            100    |         0.46 |         102.47 |        383 |
| MCD      | 1091_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           1.49 |             96    |        39.76 |         102.49 |        342 |
| MCD      | 1091_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.94 |             96    |        15.71 |         102.49 |        775 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |         0 |         nan    |            nan    |         0.69 |          85.76 |        nan |
| MCD      | 1091_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        19.63 |          85.76 |       2522 |
| MCD      | 1091_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        10.64 |          85.76 |        nan |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         0 |         nan    |            nan    |        17.7  |          88.71 |       4269 |
| MCD      | 1097_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         5.16 |          88.7  |        617 |
| MCD      | 1097_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |        10.33 |          88.71 |       1057 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        23 |          20.18 |             43.48 |        31.68 |          93.71 |        295 |
| MCD      | 1097_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        40.6  |          93.7  |        nan |
| MCD      | 1097_IriunWebcam_before  | telefon        | dinlenme         |        16 |          29.16 |              0    |        34.68 |          93.69 |        251 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        24 |           1.18 |            100    |         1.01 |          86.37 |        187 |
| MCD      | 1099_USBVideo_after      | USB (yan)      | egzersiz sonrası |        23 |           6.47 |             65.22 |        23.92 |          86.37 |        295 |
| MCD      | 1099_IriunWebcam_after   | telefon        | egzersiz sonrası |        14 |           1.19 |            100    |         8.21 |          86.37 |        808 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        22 |          15.52 |             31.82 |         1.46 |          74.33 |        998 |
| MCD      | 1099_USBVideo_before     | USB (yan)      | dinlenme         |        19 |           1.84 |             94.74 |         9.14 |          74.36 |       1160 |
| MCD      | 1099_IriunWebcam_before  | telefon        | dinlenme         |        25 |           3.01 |             84    |         8.26 |          74.34 |        816 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        19 |           1.16 |            100    |        57.89 |         123.71 |       1113 |
| MCD      | 1107_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        53.89 |         123.7  |        nan |
| MCD      | 1107_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.88 |             92    |         3.07 |         123.7  |        190 |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        26 |           1.76 |             92.31 |         1    |          89.41 |        234 |
| MCD      | 1107_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         7.39 |          89.42 |        nan |
| MCD      | 1107_IriunWebcam_before  | telefon        | dinlenme         |        26 |           2.72 |             84.62 |        24.65 |          89.4  |        202 |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        26 |           2.34 |             84.62 |         1.61 |          82.67 |        303 |
| MCD      | 1113_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          82.1  |        nan |
| MCD      | 1113_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         6.98 |          82.66 |        194 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        26 |           4.84 |             76.92 |         1.17 |          83.51 |        735 |
| MCD      | 1113_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        41.47 |          83.52 |        nan |
| MCD      | 1113_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        12.45 |          83.51 |        nan |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        26 |           2.72 |             88.46 |         1.21 |          92    |        185 |
| MCD      | 1115_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          92.04 |        nan |
| MCD      | 1115_IriunWebcam_after   | telefon        | egzersiz sonrası |        26 |           2.28 |             92.31 |        11.36 |          92.02 |        178 |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        26 |           5.62 |             73.08 |         5.5  |          75.51 |        179 |
| MCD      | 1115_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |       nan    |          75.48 |        nan |
| MCD      | 1115_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         8.23 |          75.51 |        nan |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        26 |           0.86 |            100    |         0.4  |          67.3  |        204 |
| MCD      | 1149_USBVideo_after      | USB (yan)      | egzersiz sonrası |        17 |           0.62 |            100    |         7.71 |          67.3  |        183 |
| MCD      | 1149_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         1.02 |          67.3  |        200 |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        26 |           0.53 |            100    |         0.43 |          71.36 |        187 |
| MCD      | 1149_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         4.32 |          71.36 |        539 |
| MCD      | 1149_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         1.19 |          71.37 |        617 |
