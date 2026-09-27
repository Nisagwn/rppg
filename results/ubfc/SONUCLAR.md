# UBFC-rPPG Sonuçları

Denek sayısı: 8

## En iyi 20 konfigürasyon (pencere düzeyi, 10 s)

| yöntem   | roi           | füzyon   | takip   |   MAE |   RMSE |    r |   ≤5BPM% |   video_MAE |
|:---------|:--------------|:---------|:--------|------:|-------:|-----:|---------:|------------:|
| chrom    | alın+yanaklar | snr      | argmax  |  1.53 |   2.23 | 0.88 |    96.96 |        0.64 |
| ica      | yanaklar      | mean     | argmax  |  1.57 |   2.25 | 0.9  |    96.61 |        0.53 |
| chrom    | 4_bölge       | mean     | argmax  |  1.61 |   2.55 | 0.86 |    96.37 |        0.55 |
| lgi      | tüm_yüz       | mean     | argmax  |  1.61 |   2.54 | 0.88 |    96.19 |        0.44 |
| chrom    | alın+yanaklar | mean     | argmax  |  1.62 |   2.58 | 0.85 |    96.83 |        0.51 |
| pos      | tüm_yüz       | mean     | argmax  |  1.62 |   2.55 | 0.87 |    95.73 |        0.44 |
| ica      | tüm_yüz       | mean     | argmax  |  1.63 |   2.44 | 0.88 |    96.48 |        0.55 |
| ica      | 4_bölge       | snr      | argmax  |  1.64 |   2.53 | 0.88 |    96.73 |        0.6  |
| chrom    | 4_bölge       | snr      | argmax  |  1.64 |   2.59 | 0.87 |    96.48 |        0.61 |
| ica      | alın+yanaklar | snr      | argmax  |  1.64 |   2.54 | 0.88 |    96.73 |        0.69 |
| chrom    | yanaklar      | mean     | argmax  |  1.68 |   2.63 | 0.85 |    95.78 |        0.55 |
| ica      | 4_bölge       | mean     | argmax  |  1.68 |   2.59 | 0.88 |    96.14 |        0.65 |
| pos      | 4_bölge       | mean     | argmax  |  1.68 |   2.59 | 0.87 |    95.01 |        0.46 |
| lgi      | 4_bölge       | mean     | argmax  |  1.69 |   2.59 | 0.87 |    95.26 |        0.46 |
| ica      | yanaklar      | snr      | argmax  |  1.71 |   2.82 | 0.85 |    95.97 |        0.73 |
| ica      | alın+yanaklar | mean     | argmax  |  1.72 |   2.66 | 0.87 |    96.14 |        0.69 |
| pos      | alın+yanaklar | mean     | argmax  |  1.74 |   2.67 | 0.87 |    94.79 |        0.44 |
| chrom    | tüm_yüz       | mean     | argmax  |  1.74 |   2.95 | 0.85 |    96.02 |        0.81 |
| lgi      | alın+yanaklar | snr      | viterbi |  1.81 |   2.44 | 0.9  |    93.23 |        0.7  |
| chrom    | tüm_yüz       | mean     | viterbi |  1.84 |   2.69 | 0.86 |    93.93 |        0.91 |

## Yöntem x ROI (Viterbi takip)

| yöntem   |   4_bölge |   alın |   alın+yanaklar |   tüm_yüz |   yanaklar |
|:---------|----------:|-------:|----------------:|----------:|-----------:|
| chrom    |      1.88 |   2.11 |            2.03 |      1.84 |       2.12 |
| green    |     10.42 |  18.36 |           13.47 |      7.11 |      10.74 |
| ica      |      1.92 |   2.12 |            1.99 |      1.95 |       1.98 |
| lgi      |      1.98 |   2.05 |            1.9  |      2.11 |       2.24 |
| pos      |      1.93 |   2.04 |            1.91 |      2.04 |       2.02 |
