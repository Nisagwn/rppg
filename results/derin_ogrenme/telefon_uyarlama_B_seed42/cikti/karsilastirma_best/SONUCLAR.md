# Telefon uyarlama B, seed 42 best ve Uygulama tur5

Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.
Kullanılan kümeler: mcd_uc_kamera: 48 video.
Dosya listeleri ayarlar.json'dadır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.
Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.
Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.
Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.
Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.

| test          |   hop | yöntem                                   |   video |   pencere_MAE |   video_MAE |     p5 |
|:--------------|------:|:-----------------------------------------|--------:|--------------:|------------:|-------:|
| mcd_uc_kamera |    80 | Telefon uyarlama B, seed 42 best         |      48 |         2.158 |       0.739 | 92.637 |
| mcd_uc_kamera |    80 | Telefon uyarlama B, seed 42 best+Viterbi |      48 |         1.27  |       0.739 | 94.678 |
| mcd_uc_kamera |    80 | Uygulama tur5                            |      48 |         2.158 |       0.739 | 92.637 |
| mcd_uc_kamera |    80 | Uygulama tur5+Viterbi                    |      48 |         1.27  |       0.739 | 94.678 |
| mcd_uc_kamera |   160 | Telefon uyarlama B, seed 42 best         |      48 |         2.162 |       0.681 | 92.416 |
| mcd_uc_kamera |   160 | Telefon uyarlama B, seed 42 best+Viterbi |      48 |         1.315 |       0.681 | 94.679 |
| mcd_uc_kamera |   160 | Uygulama tur5                            |      48 |         2.162 |       0.681 | 92.416 |
| mcd_uc_kamera |   160 | Uygulama tur5+Viterbi                    |      48 |         1.315 |       0.681 | 94.679 |

## Eşleştirilmiş video karşılaştırması

Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.

| test          |   hop | takip    |   n |   aday_MAE |   mevcut_MAE |   fark_aday_eksi_mevcut |   p_Wilcoxon |
|:--------------|------:|:---------|----:|-----------:|-------------:|------------------------:|-------------:|
| mcd_uc_kamera |    80 | argmax   |  48 |    2.15821 |      2.15821 |                       0 |            1 |
| mcd_uc_kamera |    80 | +Viterbi |  48 |    1.27045 |      1.27045 |                       0 |            1 |
| mcd_uc_kamera |   160 | argmax   |  48 |    2.16175 |      2.16175 |                       0 |            1 |
| mcd_uc_kamera |   160 | +Viterbi |  48 |    1.31482 |      1.31482 |                       0 |            1 |
