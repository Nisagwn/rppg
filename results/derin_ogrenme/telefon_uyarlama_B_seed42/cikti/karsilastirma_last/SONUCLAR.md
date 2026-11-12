# Telefon uyarlama B, seed 42 last ve Uygulama tur5

Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.
Kullanılan kümeler: mcd_uc_kamera: 48 video.
Dosya listeleri ayarlar.json'dadır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.
Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.
Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.
Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.
Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.

| test          |   hop | yöntem                                   |   video |   pencere_MAE |   video_MAE |     p5 |
|:--------------|------:|:-----------------------------------------|--------:|--------------:|------------:|-------:|
| mcd_uc_kamera |    80 | Telefon uyarlama B, seed 42 last         |      48 |         2.364 |       1.042 | 91.247 |
| mcd_uc_kamera |    80 | Telefon uyarlama B, seed 42 last+Viterbi |      48 |         1.503 |       1.042 | 93.176 |
| mcd_uc_kamera |    80 | Uygulama tur5                            |      48 |         2.158 |       0.739 | 92.637 |
| mcd_uc_kamera |    80 | Uygulama tur5+Viterbi                    |      48 |         1.27  |       0.739 | 94.678 |
| mcd_uc_kamera |   160 | Telefon uyarlama B, seed 42 last         |      48 |         2.39  |       1.06  | 90.89  |
| mcd_uc_kamera |   160 | Telefon uyarlama B, seed 42 last+Viterbi |      48 |         1.747 |       1.06  | 92.253 |
| mcd_uc_kamera |   160 | Uygulama tur5                            |      48 |         2.162 |       0.681 | 92.416 |
| mcd_uc_kamera |   160 | Uygulama tur5+Viterbi                    |      48 |         1.315 |       0.681 | 94.679 |

## Eşleştirilmiş video karşılaştırması

Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.

| test          |   hop | takip    |   n |   aday_MAE |   mevcut_MAE |   fark_aday_eksi_mevcut |   p_Wilcoxon |
|:--------------|------:|:---------|----:|-----------:|-------------:|------------------------:|-------------:|
| mcd_uc_kamera |    80 | argmax   |  48 |    2.36361 |      2.15821 |                 0.2054  |      0.00016 |
| mcd_uc_kamera |    80 | +Viterbi |  48 |    1.50301 |      1.27045 |                 0.23256 |      0       |
| mcd_uc_kamera |   160 | argmax   |  48 |    2.39023 |      2.16175 |                 0.22849 |      0.00032 |
| mcd_uc_kamera |   160 | +Viterbi |  48 |    1.74659 |      1.31482 |                 0.43177 |      0       |
