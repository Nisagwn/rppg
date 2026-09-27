# MCD-rPPG Sonuçları

Kişi: 10, video: 58 (kaynak: Hugging Face `akramic/mcd_rppg`, CC-BY-4.0). Pencere: 10 s. Referans: karelere hizalı parmak PPG'sinden pencere başına spektral tepe.

> Not: kamera ve bakış açısı bu veri setinde birbirine bağlıdır (webcam önden, USB kamera soldan, telefon sağdan). Kamera farkı açı farkını da içerir.

Yüz bulunamadığı için atlanan videolar (2): 1113_USBVideo_after, 1115_USBVideo_before

## En iyi 20 konfigürasyon

| yöntem   | roi           | füzyon   | takip   |   MAE |   RMSE |    r |   ≤5BPM% |   video_MAE |
|:---------|:--------------|:---------|:--------|------:|-------:|-----:|---------:|------------:|
| green    | tüm_yüz       | mean     | viterbi | 12.06 |  14.72 | 0.31 |    58.01 |       10.77 |
| pos      | tüm_yüz       | mean     | viterbi | 12.72 |  15.09 | 0.33 |    56.6  |       11.49 |
| green    | 4_bölge       | mean     | viterbi | 13.27 |  15.97 | 0.26 |    53.64 |       11.83 |
| pos      | 4_bölge       | mean     | viterbi | 13.35 |  15.71 | 0.29 |    51.22 |       11.52 |
| pos      | alın+yanaklar | mean     | viterbi | 13.5  |  15.83 | 0.29 |    49.85 |       11.47 |
| ica      | tüm_yüz       | mean     | viterbi | 14.01 |  16.61 | 0.26 |    47.84 |       11.78 |
| green    | alın+yanaklar | mean     | viterbi | 14.06 |  16.98 | 0.23 |    49.85 |       12.51 |
| pos      | tüm_yüz       | mean     | argmax  | 14.17 |  19.14 | 0.27 |    52.84 |        8.25 |
| green    | 4_bölge       | snr      | viterbi | 14.27 |  16.99 | 0.26 |    54.23 |       13.44 |
| pos      | alın          | mean     | viterbi | 14.34 |  16.76 | 0.2  |    42.45 |       12.5  |
| ica      | 4_bölge       | mean     | viterbi | 14.39 |  16.9  | 0.15 |    45.05 |       11.63 |
| pos      | yanaklar      | mean     | viterbi | 14.47 |  16.73 | 0.23 |    43.79 |       12.31 |
| green    | yanaklar      | mean     | viterbi | 14.63 |  17.68 | 0.19 |    45    |       12.95 |
| lgi      | tüm_yüz       | mean     | viterbi | 14.71 |  17.07 | 0.25 |    48.33 |       13.18 |
| ica      | alın+yanaklar | mean     | viterbi | 14.88 |  17.38 | 0.16 |    40.9  |       12.05 |
| pos      | 4_bölge       | mean     | argmax  | 14.92 |  19.89 | 0.21 |    48.21 |        8.48 |
| lgi      | 4_bölge       | mean     | viterbi | 14.94 |  17.19 | 0.23 |    46.13 |       13.35 |
| pos      | 4_bölge       | snr      | argmax  | 15.18 |  18.5  | 0.19 |    47.45 |       13.26 |
| pos      | 4_bölge       | snr      | viterbi | 15.24 |  17.08 | 0.28 |    48.16 |       14.49 |
| green    | tüm_yüz       | mean     | argmax  | 15.25 |  21.73 | 0.09 |    50.62 |        9.26 |

## Kamera x durum — MAE (BPM), POS klasik hat

| kamera           |   dinlenme |   egzersiz sonrası |
|:-----------------|-----------:|-------------------:|
| USB kamera (sol) |      17.19 |              24.98 |
| telefon (sağ)    |      14.16 |              18.09 |
| webcam (önden)   |       5.14 |               6.83 |

## Kamera x durum — MAE (BPM), POS önerilen hat

| kamera           |   dinlenme |   egzersiz sonrası |
|:-----------------|-----------:|-------------------:|
| USB kamera (sol) |      15.6  |              26.58 |
| telefon (sağ)    |      14.16 |              21.95 |
| webcam (önden)   |       5.09 |               9.24 |

Ortalama referans nabız: dinlenme 80.5 BPM, egzersiz sonrası 88.0 BPM

## Yöntem x kamera (Viterbi takip, tüm ROI setleri ortalaması)

| yöntem   |   USB kamera (sol) |   telefon (sağ) |   webcam (önden) |
|:---------|-------------------:|----------------:|-----------------:|
| chrom    |              24.92 |           20.54 |            11.85 |
| green    |              20.67 |           15.76 |             8.5  |
| ica      |              22.27 |           17.4  |            11.83 |
| lgi      |              23.24 |           18.53 |             9.13 |
| pos      |              20.28 |           16.97 |             6.74 |
