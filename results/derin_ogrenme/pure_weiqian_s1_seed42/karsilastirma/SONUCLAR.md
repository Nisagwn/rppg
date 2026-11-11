# PURE S1 ve mevcut uygulama modeli

Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.
Ana küme UBFC'nin 8 test kişisi ile MCD'nin 20 önden webcam kaydını içerir; bu küme 42 kişilik UBFC testi değildir.
Kamera kümesi MCD telefon/yan USB kayıtlarıdır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.
Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.
Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.
Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.
Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.

| test   |   hop | yöntem                |   video |   pencere_MAE |   video_MAE |     p5 |
|:-------|------:|:----------------------|--------:|--------------:|------------:|-------:|
| ana    |    80 | PURE S1 best          |      28 |         3.227 |       1.034 | 89.531 |
| ana    |    80 | PURE S1 best+Viterbi  |      28 |         2.451 |       1.034 | 90.002 |
| ana    |    80 | Uygulama tur5         |      28 |         1.264 |       0.449 | 96.564 |
| ana    |    80 | Uygulama tur5+Viterbi |      28 |         1.101 |       0.449 | 95.413 |
| ana    |   160 | PURE S1 best          |      28 |         3.295 |       1.175 | 89.132 |
| ana    |   160 | PURE S1 best+Viterbi  |      28 |         2.358 |       1.175 | 90.044 |
| ana    |   160 | Uygulama tur5         |      28 |         1.279 |       0.62  | 96.501 |
| ana    |   160 | Uygulama tur5+Viterbi |      28 |         1.098 |       0.62  | 95.839 |
| kamera |    80 | PURE S1 best          |      28 |        12.628 |      10.877 | 53.579 |
| kamera |    80 | PURE S1 best+Viterbi  |      28 |         6.665 |      10.877 | 66.078 |
| kamera |    80 | Uygulama tur5         |      28 |         2.75  |       0.838 | 89.823 |
| kamera |    80 | Uygulama tur5+Viterbi |      28 |         1.592 |       0.838 | 92.836 |
| kamera |   160 | PURE S1 best          |      28 |        12.972 |       7.727 | 51.663 |
| kamera |   160 | PURE S1 best+Viterbi  |      28 |         6.901 |       7.727 | 64.473 |
| kamera |   160 | Uygulama tur5         |      28 |         2.739 |       0.705 | 89.591 |
| kamera |   160 | Uygulama tur5+Viterbi |      28 |         1.641 |       0.705 | 92.838 |

## Eşleştirilmiş video karşılaştırması

Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.

| test   |   hop | takip    |   n |   aday_MAE |   mevcut_MAE |   fark_aday_eksi_mevcut |   p_Wilcoxon |
|:-------|------:|:---------|----:|-----------:|-------------:|------------------------:|-------------:|
| ana    |    80 | argmax   |  28 |    3.22673 |      1.26414 |                 1.96258 |      1e-05   |
| ana    |    80 | +Viterbi |  28 |    2.45082 |      1.10083 |                 1.34999 |      0.00053 |
| ana    |   160 | argmax   |  28 |    3.295   |      1.27942 |                 2.01559 |      0       |
| ana    |   160 | +Viterbi |  28 |    2.35832 |      1.09841 |                 1.25991 |      0.00011 |
| kamera |    80 | argmax   |  28 |   12.6281  |      2.74981 |                 9.87831 |      0       |
| kamera |    80 | +Viterbi |  28 |    6.66525 |      1.59158 |                 5.07368 |      0       |
| kamera |   160 | argmax   |  28 |   12.972   |      2.73916 |                10.2328  |      0       |
| kamera |   160 | +Viterbi |  28 |    6.90141 |      1.64104 |                 5.26038 |      0       |
