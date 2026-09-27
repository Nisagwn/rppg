# Sentetik Benchmark Sonuçları

- Senaryo sayısı: 9, tohum: 3, video süresi: 60 s
- Pencere: 10 s, adım: 1 s. Metrikler pencere düzeyinde, video ve tohumlar üzerinden ortalama.

## A. Klasik yöntemler — senaryo bazında MAE (BPM), tüm yüz ROI + argmax

|       |   İdeal |   Sensör gürültüsü |   Beyaz ışık dalgalanması |   Renkli ekran ışığı (global) |   JPEG sıkıştırma (q=70) |   Baş hareketi |   Saç örtmesi (alın) |   Yanakta renkli titreme |   Hepsi birden |
|:------|--------:|-------------------:|--------------------------:|------------------------------:|-------------------------:|---------------:|---------------------:|-------------------------:|---------------:|
| CHROM |    0.58 |               0.66 |                      0.7  |                          0.74 |                     1.01 |           0.59 |                 0.63 |                     0.77 |          32.97 |
| GREEN |    0.58 |               0.57 |                     32.2  |                         24.72 |                     0.6  |          36.13 |                 1.26 |                    25.85 |          22.81 |
| ICA   |   19.93 |              13.71 |                      0.59 |                         19.93 |                    23.53 |           0.56 |                16.67 |                    19.66 |          11.07 |
| LGI   |    0.57 |               0.63 |                      0.58 |                         17.65 |                     0.83 |           0.56 |                 0.57 |                    24.83 |          26.55 |
| POS   |    0.57 |               0.6  |                      0.58 |                          0.74 |                     0.8  |           0.56 |                 0.57 |                     0.76 |          11.63 |

## B. Ablasyon — POS yöntemiyle ROI / füzyon / takip (MAE, BPM)

|                                         |   İdeal |   Sensör gürültüsü |   Beyaz ışık dalgalanması |   Renkli ekran ışığı (global) |   JPEG sıkıştırma (q=70) |   Baş hareketi |   Saç örtmesi (alın) |   Yanakta renkli titreme |   Hepsi birden |   ORTALAMA |
|:----------------------------------------|--------:|-------------------:|--------------------------:|------------------------------:|-------------------------:|---------------:|---------------------:|-------------------------:|---------------:|-----------:|
| Tüm yüz + argmax (klasik)               |    0.57 |               0.6  |                      0.58 |                          0.74 |                     0.8  |           0.56 |                 0.57 |                     0.76 |          11.63 |       1.87 |
| Alın + argmax                           |    0.57 |               1.36 |                      0.63 |                          0.78 |                     7.15 |           0.65 |                49.55 |                     0.81 |          24.15 |       9.52 |
| 3 ROI ortalama + argmax                 |    0.56 |               0.62 |                      0.59 |                          0.74 |                     0.7  |           0.58 |                 0.58 |                     0.78 |          18.35 |       2.61 |
| 3 ROI SNR füzyon + argmax               |    0.56 |               0.62 |                      0.59 |                          0.74 |                     0.81 |           0.58 |                 0.56 |                     0.76 |           9.45 |       1.63 |
| 3 ROI ortalama + Viterbi                |    0.56 |               0.62 |                      0.59 |                          0.74 |                     0.7  |           0.58 |                 0.58 |                     0.78 |           3.09 |       0.92 |
| 3 ROI SNR füzyon + Viterbi              |    0.56 |               0.62 |                      0.59 |                          0.74 |                     0.81 |           0.58 |                 0.56 |                     0.76 |           2.88 |       0.9  |
| Tüm yüz + Viterbi                       |    0.57 |               0.6  |                      0.58 |                          0.74 |                     0.8  |           0.56 |                 0.57 |                     0.76 |           1.15 |       0.7  |
| 4 bölge SNR füzyon + argmax             |    0.56 |               0.58 |                      0.58 |                          0.74 |                     0.76 |           0.56 |                 0.55 |                     0.74 |           6.54 |       1.29 |
| 4 bölge SNR füzyon + Viterbi (önerilen) |    0.56 |               0.58 |                      0.58 |                          0.74 |                     0.76 |           0.56 |                 0.55 |                     0.74 |           1.22 |       0.7  |

## C. Tüm konfigürasyonlar içinde en iyi 15 (ortalama MAE)

| yöntem   | roi           | füzyon   | takip   |   MAE |   RMSE |    r |   ≤5BPM% |   video_MAE |
|:---------|:--------------|:---------|:--------|------:|-------:|-----:|---------:|------------:|
| pos      | 4_bölge       | snr      | viterbi |  0.7  |   0.86 | 0.98 |   100    |        0.05 |
| pos      | tüm_yüz       | mean     | viterbi |  0.7  |   0.87 | 0.98 |    99.93 |        0.04 |
| pos      | yanaklar      | mean     | viterbi |  0.72 |   0.88 | 0.98 |   100    |        0.05 |
| pos      | 4_bölge       | mean     | viterbi |  0.72 |   0.88 | 0.98 |   100    |        0.05 |
| pos      | yanaklar      | snr      | viterbi |  0.89 |   1.16 | 0.94 |    98.84 |        0.22 |
| pos      | alın+yanaklar | snr      | viterbi |  0.9  |   1.18 | 0.97 |    98.91 |        0.24 |
| pos      | alın+yanaklar | mean     | viterbi |  0.92 |   1.23 | 0.94 |    98.55 |        0.23 |
| pos      | 4_bölge       | snr      | argmax  |  1.29 |   2.66 | 0.89 |    98.62 |        0.48 |
| pos      | alın+yanaklar | snr      | argmax  |  1.63 |   2.73 | 0.9  |    96.88 |        0.38 |
| pos      | yanaklar      | snr      | argmax  |  1.8  |   3.13 | 0.92 |    97.46 |        0.97 |
| pos      | tüm_yüz       | mean     | argmax  |  1.87 |   3.91 | 0.91 |    98.4  |        1.21 |
| ica      | 4_bölge       | snr      | viterbi |  1.87 |   2.21 | 0.91 |    92.67 |        1.26 |
| pos      | yanaklar      | mean     | argmax  |  2.44 |   4.09 | 0.9  |    96.88 |        1.59 |
| chrom    | yanaklar      | snr      | viterbi |  2.47 |   2.98 | 0.84 |    91.36 |        1.14 |
| pos      | 4_bölge       | mean     | argmax  |  2.53 |   4.08 | 0.9  |    96.44 |        1.63 |

## D. Her yöntem için: klasik (tüm yüz+argmax) vs önerilen (4 bölge SNR füzyon + Viterbi)

| yöntem   |   klasik MAE |   önerilen MAE |   iyileşme % |
|:---------|-------------:|---------------:|-------------:|
| GREEN    |        16.08 |          11.91 |        25.94 |
| ICA      |        13.96 |           1.87 |        86.59 |
| CHROM    |         4.29 |           2.6  |        39.46 |
| POS      |         1.87 |           0.7  |        62.6  |
| LGI      |         8.09 |           2.99 |        62.99 |

## H. Solunum hızı mutlak hatası (nefes/dk)

|                             |   MAE |
|:----------------------------|------:|
| İdeal                       |  0    |
| Sensör gürültüsü            |  0    |
| Beyaz ışık dalgalanması     |  0    |
| Renkli ekran ışığı (global) |  0    |
| JPEG sıkıştırma (q=70)      |  0    |
| Baş hareketi                |  0.02 |
| Saç örtmesi (alın)          |  0    |
| Yanakta renkli titreme      |  0    |
| Hepsi birden                |  0.02 |

Genel solunum MAE: **0.01 nefes/dk**
