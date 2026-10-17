# Mobil Uygulama — Gerçek Veri Doğrulaması

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | USB (yan)      | dinlenme         |      10 |           5.76 |             77.14 |        14.67 |
| MCD      | USB (yan)      | egzersiz sonrası |      10 |           3.39 |             89.91 |        20.73 |
| MCD      | telefon        | dinlenme         |      10 |           2.63 |             86.32 |        12.38 |
| MCD      | telefon        | egzersiz sonrası |      10 |           2.04 |             90.89 |         8.3  |
| MCD      | webcam (önden) | dinlenme         |      10 |           4.26 |             82.26 |         4.49 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |           2.21 |             90.4  |         8.29 |

**Genel:** uygulama MAE 3.14 BPM, pencerelerin %87'i ≤5 BPM; aynı kesitlerde Python hattı MAE 11.10 BPM (60 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        22 |           4.38 |             63.64 |         0.58 |          77.5  |
| MCD      | 1020_USBVideo_after      | USB (yan)      | egzersiz sonrası |        11 |           2.14 |             90.91 |        10.09 |          77.5  |
| MCD      | 1020_IriunWebcam_after   | telefon        | egzersiz sonrası |        15 |           3.18 |             80    |         8.49 |          77.51 |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        11 |           2.09 |            100    |         0.73 |          75.37 |
| MCD      | 1020_USBVideo_before     | USB (yan)      | dinlenme         |        20 |           4.37 |             75    |         4.74 |          75.37 |
| MCD      | 1020_IriunWebcam_before  | telefon        | dinlenme         |         8 |           1.06 |            100    |         1.14 |          75.37 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |         8 |           2.2  |            100    |         1.23 |          69.16 |
| MCD      | 1024_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        22.21 |          69.16 |
| MCD      | 1024_IriunWebcam_after   | telefon        | egzersiz sonrası |        17 |           2.69 |             88.24 |        13.11 |          69.16 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           1.74 |            100    |         0.73 |          74.74 |
| MCD      | 1024_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         1.18 |          74.75 |
| MCD      | 1024_IriunWebcam_before  | telefon        | dinlenme         |        22 |           3.59 |             72.73 |        18.91 |          74.75 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        24 |           1.43 |            100    |         0.76 |          74.39 |
| MCD      | 1035_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         3.11 |          74.38 |
| MCD      | 1035_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.34 |             84    |         4.67 |          74.38 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        23 |           0.79 |            100    |         1.54 |          68.91 |
| MCD      | 1035_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         3.6  |          68.9  |
| MCD      | 1035_IriunWebcam_before  | telefon        | dinlenme         |        25 |           1.4  |            100    |         3.7  |          68.91 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.31 |             96    |         0.46 |         102.47 |
| MCD      | 1091_USBVideo_after      | USB (yan)      | egzersiz sonrası |        16 |           9.08 |             68.75 |        39.76 |         102.49 |
| MCD      | 1091_IriunWebcam_after   | telefon        | egzersiz sonrası |         8 |           0.42 |            100    |        15.71 |         102.49 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |         5 |           3.38 |            100    |         0.69 |          85.76 |
| MCD      | 1091_USBVideo_before     | USB (yan)      | dinlenme         |        14 |           3.66 |             71.43 |        19.63 |          85.76 |
| MCD      | 1091_IriunWebcam_before  | telefon        | dinlenme         |        10 |           2.11 |             90    |        10.64 |          85.76 |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        24 |           2.6  |             87.5  |        17.7  |          88.71 |
| MCD      | 1097_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |         5.16 |          88.7  |
| MCD      | 1097_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |        10.33 |          88.71 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        19 |           8.07 |             63.16 |        31.68 |          93.71 |
| MCD      | 1097_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        40.6  |          93.7  |
| MCD      | 1097_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        34.68 |          93.69 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        23 |           1.11 |            100    |         1.01 |          86.37 |
| MCD      | 1099_USBVideo_after      | USB (yan)      | egzersiz sonrası |        19 |           1.72 |            100    |        23.92 |          86.37 |
| MCD      | 1099_IriunWebcam_after   | telefon        | egzersiz sonrası |        24 |           1.47 |            100    |         8.21 |          86.37 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        24 |           2.31 |             79.17 |         1.46 |          74.33 |
| MCD      | 1099_USBVideo_before     | USB (yan)      | dinlenme         |        20 |           9.26 |             85    |         9.14 |          74.36 |
| MCD      | 1099_IriunWebcam_before  | telefon        | dinlenme         |        23 |           5.24 |             73.91 |         8.26 |          74.34 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           0.82 |            100    |        57.89 |         123.71 |
| MCD      | 1107_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |        53.89 |         123.7  |
| MCD      | 1107_IriunWebcam_after   | telefon        | egzersiz sonrası |        21 |           1.12 |            100    |         3.07 |         123.7  |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        22 |           3.85 |             68.18 |         1    |          89.41 |
| MCD      | 1107_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         7.39 |          89.42 |
| MCD      | 1107_IriunWebcam_before  | telefon        | dinlenme         |        16 |           2.41 |             81.25 |        24.65 |          89.4  |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        24 |           3.83 |             75    |         1.61 |          82.67 |
| MCD      | 1113_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          82.1  |
| MCD      | 1113_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         6.98 |          82.66 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        23 |           5.92 |             69.57 |         1.17 |          83.51 |
| MCD      | 1113_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |        41.47 |          83.52 |
| MCD      | 1113_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |        12.45 |          83.51 |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        22 |           3.33 |             81.82 |         1.21 |          92    |
| MCD      | 1115_USBVideo_after      | USB (yan)      | egzersiz sonrası |         0 |         nan    |            nan    |       nan    |          92.04 |
| MCD      | 1115_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           3.02 |             84    |        11.36 |          92.02 |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        20 |           8.58 |             55    |         5.5  |          75.51 |
| MCD      | 1115_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |       nan    |          75.48 |
| MCD      | 1115_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         8.23 |          75.51 |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        11 |           1.06 |            100    |         0.4  |          67.3  |
| MCD      | 1149_USBVideo_after      | USB (yan)      | egzersiz sonrası |        15 |           0.61 |            100    |         7.71 |          67.3  |
| MCD      | 1149_IriunWebcam_after   | telefon        | egzersiz sonrası |         0 |         nan    |            nan    |         1.02 |          67.3  |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        24 |           5.91 |             87.5  |         0.43 |          71.36 |
| MCD      | 1149_USBVideo_before     | USB (yan)      | dinlenme         |         0 |         nan    |            nan    |         4.32 |          71.36 |
| MCD      | 1149_IriunWebcam_before  | telefon        | dinlenme         |         0 |         nan    |            nan    |         1.19 |          71.37 |
