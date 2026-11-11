# iBVP FactorizePhys FSAM on diagnostic ve Uygulama tur5

Her iki model aynı yerel test kayıtları ve aynı 72×72 yüz kırpıntıları üzerinde yeniden çalıştırıldı.
Kullanılan kümeler: ana: 28 video; kamera: 28 video.
Dosya listeleri ayarlar.json'dadır. Yüz kalitesi filtresinden geçen gerçek sayılar tabloda verilir.
Hop 80 uygulamadaki %50 örtüşmeye karşılık gelir; hop 160 önceki çevrimdışı protokoldür.
Pencere MAE: her videonun pencere hatası hesaplanıp videolar eşit ağırlıkla ortalanır.
Video MAE: bütün kaydın spektral tepesinin mutlak hatasıdır; Viterbi bu sütunu değiştirmez.
Bu ölçüm telefon tarayıcısının hızını veya canlı kullanıcı performansını ölçmez.

Yeni çıkarım aygıtı: cpu. Temel model önbelleği: results/derin_ogrenme/pure_weiqian_s1_seed42/karsilastirma/test_sonuclari.csv.

Ağ ayarları ve yüklenmeyen ağırlıklar ayarlar.json'da kayıtlıdır. Ortak yüz kırpıntıları kullanıldığı için bu sonuçlar yazarların tüm ön işleme hattının yeniden üretimi değildir.

| test   |   hop | yöntem                                        |   video |   pencere_MAE |   video_MAE |     p5 |
|:-------|------:|:----------------------------------------------|--------:|--------------:|------------:|-------:|
| ana    |    80 | Uygulama tur5                                 |      28 |         1.264 |       0.449 | 96.564 |
| ana    |    80 | Uygulama tur5+Viterbi                         |      28 |         1.101 |       0.449 | 95.413 |
| ana    |    80 | iBVP FactorizePhys FSAM on diagnostic         |      28 |         3.999 |       0.574 | 87.959 |
| ana    |    80 | iBVP FactorizePhys FSAM on diagnostic+Viterbi |      28 |         2.502 |       0.574 | 90.639 |
| kamera |    80 | Uygulama tur5                                 |      28 |         2.75  |       0.838 | 89.823 |
| kamera |    80 | Uygulama tur5+Viterbi                         |      28 |         1.592 |       0.838 | 92.836 |
| kamera |    80 | iBVP FactorizePhys FSAM on diagnostic         |      28 |        10.789 |       6.576 | 53.355 |
| kamera |    80 | iBVP FactorizePhys FSAM on diagnostic+Viterbi |      28 |         7.923 |       6.576 | 62.307 |

## Eşleştirilmiş video karşılaştırması

Negatif fark aday lehine. p değerleri çoklu karşılaştırma düzeltmesi yapılmadan, keşif amaçlı verilmiştir.

| test   |   hop | takip    |   n |   aday_MAE |   mevcut_MAE |   fark_aday_eksi_mevcut |   p_Wilcoxon |
|:-------|------:|:---------|----:|-----------:|-------------:|------------------------:|-------------:|
| ana    |    80 | argmax   |  28 |    3.9992  |      1.26414 |                 2.73506 |      2e-05   |
| ana    |    80 | +Viterbi |  28 |    2.50207 |      1.10083 |                 1.40124 |      0.00027 |
| kamera |    80 | argmax   |  28 |   10.7894  |      2.74981 |                 8.03956 |      0       |
| kamera |    80 | +Viterbi |  28 |    7.92256 |      1.59158 |                 6.33099 |      0       |
