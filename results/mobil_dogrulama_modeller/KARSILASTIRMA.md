# Mobil Uygulama — Model Karşılaştırması (gerçek veri, tarayıcıda)

Kapsama: üretilen pencere / (kesit × 25). MAE: kesit başına ortalama (pencere üretmeyen kesit hariç).

## Kamera başına

| model   | kamera         |   kesit |   pencereli_kesit |   kapsama_% |   MAE |   ≤5BPM_% |   model_ms_medyan |
|:--------|:---------------|--------:|------------------:|------------:|------:|----------:|------------------:|
| tur3    | USB (yan)      |      20 |                 6 |       21.6  |  2.26 |     84.77 |               913 |
| tur3    | telefon        |      20 |                14 |       57.6  |  2.39 |     90.62 |               442 |
| tur3    | webcam (önden) |      20 |                18 |       80.6  |  6.2  |     74.09 |               463 |
| tur3    | hepsi          |      60 |                38 |       53.27 |  4.17 |     81.87 |               509 |
| tur5    | USB (yan)      |      20 |                 7 |       28.6  |  2.08 |     92.47 |               820 |
| tur5    | telefon        |      20 |                16 |       52.8  |  4.8  |     76.36 |               564 |
| tur5    | webcam (önden) |      20 |                18 |       74.8  |  4.83 |     75.52 |               543 |
| tur5    | hepsi          |      60 |                41 |       52.07 |  4.35 |     78.74 |               584 |
| 7E      | USB (yan)      |      20 |                 6 |       23.8  |  3.39 |     79.61 |               617 |
| 7E      | telefon        |      20 |                13 |       49.4  |  4.15 |     84.73 |               279 |
| 7E      | webcam (önden) |      20 |                18 |       83.4  |  4.06 |     84.61 |               383 |
| 7E      | hepsi          |      60 |                37 |       52.2  |  3.98 |     83.84 |               409 |

## Eşleştirilmiş Wilcoxon (kesit başına; MAE yalnızca iki modelin de pencere ürettiği kesitlerde)

| A    | B    | kamera         |   ortak_kesit |   A_MAE |   B_MAE |   A_iyi(>0.5) |   B_iyi(>0.5) |   p_MAE |   A_pencere |   B_pencere |   p_pencere |
|:-----|:-----|:---------------|--------------:|--------:|--------:|--------------:|--------------:|--------:|------------:|------------:|------------:|
| tur3 | tur5 | USB (yan)      |             6 |   2.26  |   2.093 |             0 |             2 |   0.562 |         108 |         143 |       0.225 |
| tur3 | tur5 | telefon        |            14 |   2.387 |   5.344 |             5 |             2 |   0.268 |         288 |         264 |       0.608 |
| tur3 | tur5 | webcam (önden) |            17 |   5.407 |   4.945 |             4 |             3 |   0.712 |         403 |         374 |       0.107 |
| tur3 | tur5 | hepsi          |            37 |   3.754 |   4.634 |             9 |             7 |   0.378 |         799 |         781 |       0.553 |
| tur3 | 7E   | USB (yan)      |             6 |   2.26  |   3.387 |             2 |             1 |   0.688 |         108 |         119 |       0.461 |
| tur3 | 7E   | telefon        |            13 |   2.381 |   4.15  |             5 |             2 |   0.542 |         288 |         247 |       0.693 |
| tur3 | 7E   | webcam (önden) |            17 |   5.407 |   4.215 |             3 |             4 |   0.678 |         403 |         417 |       0.895 |
| tur3 | 7E   | hepsi          |            36 |   3.79  |   4.053 |            10 |             7 |   0.715 |         799 |         783 |       0.835 |
| tur5 | 7E   | USB (yan)      |             6 |   2.093 |   3.387 |             2 |             0 |   0.688 |         143 |         119 |       0.463 |
| tur5 | 7E   | telefon        |            13 |   5.169 |   4.15  |             4 |             3 |   0.893 |         264 |         247 |       0.377 |
| tur5 | 7E   | webcam (önden) |            18 |   4.827 |   4.065 |             2 |             8 |   0.081 |         374 |         417 |       0.036 |
| tur5 | 7E   | hepsi          |            37 |   4.504 |   3.985 |             8 |            11 |   0.338 |         781 |         783 |       0.782 |

## Yöntem notları

- Modeller: 3. tur FactorizePhys (`kaggle_tur3/last.pth`, v12 uygulamasındaki dosyayla bayt bayt aynı), 5. tur
  FactorizePhys (`kaggle_tur5/last.pth`), 7. tur E MMRPhys (`kaggle_tur7_E/last.pth`). ONNX çıktısı PyTorch ile
  rastgele girdide korelasyon 1.000000, en büyük fark 3.5e-5 / 4.7e-5 / 1.7e-4. Girdi [1,3,161,72,72], çıktı [1,160]
  üçünde de aynı (MMRPhys LEF de model içinde fark alıyor; çıkarımda etiket gerekmiyor, MD_INFERENCE False).
- Her kesit üç modelle **art arda** ölçüldü, sıra kesit başına döndürüldü (`validate_mobile.py --models`); aday model
  `e2e.mjs --model` ile uygulama dosyası değiştirilmeden sunuldu. Yüz bulucu değiştirilmedi.
- Koşu sırasında makinede başka işler (başka bir doğrulama, yüz bulucu benzetimleri) çalışıyordu; tarayıcıdaki
  çıkarım süresi 300–5000 ms arasında oynadı. Ölçümler gerçek zamanlı olduğu için yük kapsama ve hatayı etkiliyor;
  art arda ölçüm bu etkiyi modellere eşit dağıtmak için. İlk 14 kesit GPU açık, kalan 46 kesit `--disable-gpu`
  ile ölçüldü (ORT her durumda wasm arka ucunda; GPU yalnızca tuval çizimini etkileyebilir, kesit içi karşılaştırma
  eşleştirilmiş kalıyor).
- Tekrar gürültüsü büyük: aynı kesit aynı modelle iki koşuda 1.28 / 2.42 BPM (5. tur), 3.65 / 4.86 (7E) verdi; tek
  bir koşuda takip yanlış tepeye kilitlenip 123 BPM gösterdi (sonraki iki tekrarda 77 / 76). 10 BPM üstü kesit
  sayısı tur3 2, tur5 4, 7E 3 ve hep farklı kesitler: modele değil koşuya bağlı aykırılar.

## Sonuç

- Üç modelin de pencere ürettiği 36 kesitte Friedman p = 0.56; ikili Wilcoxon'ların hiçbiri anlamlı değil (en küçük
  p: önden webcam 5. tur vs 7E, MAE 4.83 / 4.07, p = 0.081; pencere sayısı p = 0.036, 7E lehine). Medyan kesit MAE:
  tur3 2.24, tur5 2.42, 7E 2.09. Aynı 3. tur modelinin bu koşusu ile v12 koşusu arasında da fark anlamlı değil
  (37 kesit, 3.17 / 4.16, p = 0.69): uygulama içi ölçüm modelleri ayıracak duyarlılıkta değil.
- Kapsama modelden bağımsız (%52–53; yüz bulucu belirliyor).
- Tarayıcıda çıkarım (medyan, tek iş parçacığı wasm): tur3 509 ms, tur5 584 ms, 7E 409 ms. tur3/tur5 aynı mimari
  olduğundan aralarındaki fark yük gürültüsü; CPU'da onnxruntime tek iş parçacığı: 446 / 514 / 424 ms.
- **Karar: 7E (MMRPhys).** Uygulamada fark olmadığından seçim çevrimdışı büyük test kümelerine ve pratiğe göre:
  ana testte eşit (tur3 / tur5 / 7E: 1.13 / 1.10 / 1.13), DLCN ve VIPL testlerinde çok daha iyi (7E / tur5: DLCN
  1.31 / 2.83, VIPL 3.57 / 5.23; 7E bu veri setlerinin eğitim kişilerini gördü, 5. tur görmedi — yani kişi ve
  kamera çeşitliliği daha geniş bir eğitimin sonucu; 7B'de DLCN görülmeden de 1.69 / 2.83, p < 0.001), daha küçük (163 / 246 KB) ve daha hızlı. Bedeli: çevrimdışı telefon/USB'de 5. tur daha iyi (1.64 / 2.04,
  p = 0.001). **Lisans:** MMRPhys yalnızca araştırma amaçlı kullanıma izin veren RAIL lisanslı; uygulama herkese
  açık yayınlanacaksa bu kabul edilmeli, edilmezse yedek seçenek 5. tur FactorizePhys (rPPG-Toolbox, Responsible
  AI Source Code License).
