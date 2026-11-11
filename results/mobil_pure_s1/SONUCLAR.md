# Yerel Chrome: PURE S1 / mevcut model

Aynı ham MCD video kesitleri 30 fps sahte kamerayla uygulamaya verildi. Yüz bulma ve nabız takibi uygulamanın kendisidir.
Her model ayrı, temiz tarayıcı oturumunda `ep=wasm` ve çapraz köken yalıtımıyla çalıştırıldı.
Referans, aynı 10 s penceresindeki parmak PPG nabzıdır. İlk 10 s hariç; çıktı üretmeyen saniyeler pencere sayısına yansır.
Süre sütunu saniyelik teşhis kayıtlarındaki son model çağrısının medyanıdır; telefon performansı değildir.
Üç kesit tek kişidendir; genelleme veya istatistiksel üstünlük sonucu çıkarılamaz.
Test aracı `--expect 0` kullandığı için konsoldaki BAŞARISIZ etiketi sıfır nabız beklentisine aittir; model yüklenmesi ve gerçek PPG hatası burada ayrıca kontrol edilir.

| kesit                    | kamera         | model   |   pencere |    MAE |   p5 |   model_ms_medyan |   threads |
|:-------------------------|:---------------|:--------|----------:|-------:|-----:|------------------:|----------:|
| 1020_FullHDwebcam_before | webcam (önden) | tur5    |        25 |  1.548 |   96 |           383.015 |         4 |
| 1020_FullHDwebcam_before | webcam (önden) | pure    |        25 | 10.61  |   44 |           242.293 |         4 |
| 1020_USBVideo_before     | USB (yan)      | tur5    |        25 |  2.018 |   92 |           393.72  |         4 |
| 1020_USBVideo_before     | USB (yan)      | pure    |        25 |  3.739 |   68 |           239.83  |         4 |
| 1020_IriunWebcam_before  | telefon        | tur5    |        25 |  1.207 |  100 |           416.103 |         4 |
| 1020_IriunWebcam_before  | telefon        | pure    |        25 |  1.32  |  100 |           258.67  |         4 |
