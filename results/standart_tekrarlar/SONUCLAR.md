# Standart protokol tekrarları

Her koşuda checkpoint PURE/UBFC eğitim kaynağının doğrulama kişilerine göre seçilir; hedef teste göre seçilmez.
Tek tohumla standart sapma hesaplanmaz. Başlangıç planı: her protokol için 42, 43, 44.
Bu tablo yalnızca verilen ve tamamlanmış koşuları içerir; eksik eğitimler yapılmış sayılmaz.

| protocol   |   seed | checkpoint   |   epoch |   completed_epochs |   window_MAE |   video_MAE |   video_RMSE |   n_test | run                                          |
|:-----------|-------:|:-------------|--------:|-------------------:|-------------:|------------:|-------------:|---------:|:---------------------------------------------|
| S1         |     42 | best         |       2 |                 30 |         0.69 |        0.89 |         2.69 |       42 | results\derin_ogrenme\pure_weiqian_s1_seed42 |

| protocol   |   n_seeds |   window_MAE_mean |   window_MAE_std |   video_MAE_mean |   video_MAE_std |
|:-----------|----------:|------------------:|-----------------:|-----------------:|----------------:|
| S1         |         1 |              0.69 |              nan |             0.89 |             nan |
