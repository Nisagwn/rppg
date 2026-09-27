# Mobil Uygulama — Gerçek Veri Doğrulaması

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | webcam (önden) | dinlenme         |      10 |           5.66 |             65.69 |         7.98 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |          11.89 |             39.29 |        11.52 |
| UBFC     | webcam (önden) | oyun             |       8 |           2.02 |             91.07 |         2.47 |

**Genel:** uygulama MAE 6.84 BPM, pencerelerin %64'i ≤5 BPM; aynı kesitlerde Python hattı MAE 7.67 BPM (28 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|
| UBFC     | subject1                 | webcam (önden) | oyun             |        28 |           2.39 |            100    |         2.49 |         106.08 |
| UBFC     | subject10                | webcam (önden) | oyun             |        28 |           0.7  |            100    |         1.09 |         107.87 |
| UBFC     | subject11                | webcam (önden) | oyun             |        28 |           1.66 |             89.29 |         1.55 |         120.36 |
| UBFC     | subject3                 | webcam (önden) | oyun             |        28 |           4.91 |             64.29 |         6.67 |          94.15 |
| UBFC     | subject4                 | webcam (önden) | oyun             |        28 |           3.42 |             82.14 |         4.38 |         106.82 |
| UBFC     | subject5                 | webcam (önden) | oyun             |        28 |           0.98 |            100    |         1.11 |          99.54 |
| UBFC     | subject8                 | webcam (önden) | oyun             |        28 |           1.38 |             96.43 |         1.03 |         111.9  |
| UBFC     | subject9                 | webcam (önden) | oyun             |        28 |           0.68 |             96.43 |         1.44 |         111.16 |
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |           3.45 |             75    |         3.28 |          77.5  |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           3.75 |             64.29 |         3.73 |          75.37 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |           2.9  |             75    |         4.42 |          69.16 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           1.97 |            100    |         2.13 |          74.74 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |           8    |             42.86 |         5.55 |          74.39 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           3.16 |             78.57 |         2.73 |          68.91 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |          11.83 |              3.57 |        11.6  |         102.47 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           1.92 |             96.43 |         2.22 |          85.76 |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |          20.91 |              0    |        31.28 |          88.71 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |          17.65 |             25    |        37.76 |          93.71 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |           8.27 |             25    |         8.17 |          86.37 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           4.77 |             57.14 |         4.29 |          74.33 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        27 |          44.59 |              0    |        29.27 |         123.71 |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           9.06 |             17.86 |        12.69 |          89.41 |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |          12.5  |              7.14 |        12.02 |          82.67 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           6.5  |             53.57 |         6.33 |          83.51 |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        28 |           5    |             64.29 |         5.16 |          92    |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           6.3  |             64    |         5.97 |          75.51 |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        17 |           1.45 |            100    |         4.44 |          67.3  |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        28 |           1.53 |            100    |         2    |          71.36 |
