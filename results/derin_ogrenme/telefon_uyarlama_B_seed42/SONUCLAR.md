# Telefon uyarlama B — seed 42

12 Kasım 2026. Kaynak: kullanıcının indirdiği `results (18).zip`. Bu arşiv önceki PURE çıktısı değil; telefon uyarlama B deneyidir. Eğitim 20 epoch ve epoch başına 300 adımı tamamlamış.

## Sonuç ve karar

**Bu koşu mevcut tur5 modelini iyileştirmedi.** Son ağırlıklar değişmiş, fakat test hatası artmış. Doğrulamada hiçbir epoch başlangıç modelini geçemediğinden `best.pth` başlangıç ağırlıklarını korumuş. Uygulamadaki modeli değiştirmiyoruz.

Birincil karşılaştırma: aynı 48 MCD kaydı, 160 karelik pencereler, hop=80 (%50 örtüşme), Viterbi. Pencere hataları önce her kayıt içinde, ardından kayıtlar eşit ağırlıkla ortalanır. Küçük MAE daha iyidir.

| Model | Pencere MAE (BPM) | ±5 BPM içinde (%) |
| --- | ---: | ---: |
| Mevcut tur5 | 1.2704 | 94.68 |
| B `best.pth` — başlangıç / epoch 0 | 1.2704 | 94.68 |
| B `last.pth` — epoch 20 | 1.5030 | 93.18 |

Son modelde hata 0.2326 BPM, yaklaşık %18.3 artmış. Bütün video üzerinden hesaplanan ayrı spektral MAE de tur5 için 0.7388, son model için 1.0416 BPM. Bu ölçüt pencere MAE'siyle karıştırılmamalı. Örtüşmesiz hop=160 kontrolünde Viterbi pencere MAE'si 1.3148'den 1.7466 BPM'ye çıkıyor.

## Kamera bazında

| Kamera | Kayıt | Tur5 MAE (BPM) | B son model MAE (BPM) |
| --- | ---: | ---: | ---: |
| FullHDwebcam | 20 | 0.8209 | 0.9121 |
| IriunWebcam | 19 | 1.6575 | 2.0705 |
| USBVideo | 9 | 1.4523 | 1.6183 |

Üç kamera grubunda da son modelin ortalama hatası daha yüksek. Sayısal kaynak: [kamera_ozeti.csv](kamera_ozeti.csv).

## Eğitimin gerçekten çalıştığının kontrolü

- Başlangıç checkpoint SHA-256 değeri deney kaydıyla aynı: `0d545d62af0597b1f3bfe5225f5bac83e7348752d9bd865067cf545781e9c8ef`.
- CPU'da `torch.equal` ile karşılaştırılan 16 state-dict tensörünün tamamı `best.pth` ile tur5 arasında birebir aynı. Son checkpoint'te ise 16 tensörün tamamı değişmiş.
- `gecmis.json`: başlangıç doğrulama MAE'si **1.9475 BPM**, seçilen en iyi epoch **0**, son epoch **20**, son doğrulama MAE'si **2.1695 BPM**. Eğitim günlüğü `bitti` ile sonlanıyor.
- Eğitim kodu ilk doğrulamayı epoch 0 olarak kaydediyor; yalnız daha düşük doğrulama hatasında `best.pth` değişiyor. Bu nedenle başlangıç ağırlıklarının korunması beklenen seçim davranışı.

[Makine tarafından okunabilir kontrol ve dosya hashleri](kontrol.json), [orijinal eğitim geçmişi](cikti/gecmis.json), [eğitim günlüğü](cikti/gunlukler/egitim.log).

## Veri ve yorum sınırı

Deney manifestinde 90 eğitim, 10 doğrulama ve 10 test kişisi var; bu üç kişi listesi kesişmiyor. Eğitim ve doğrulama girdisi birlikte 100 kişiden 600 kayıt içeriyor. `--val-max 40` ayarı altında model seçimi 39 doğrulama kaydıyla yapılmış. Test için hazırlanan 60 kaydın yüz kalitesi filtresinden geçen 48'i ölçülmüş; kalan 12 kayıt sonuç ortalamasında yok. Değerlendirilen 48 kayıt 10 kişiye ait; farklı kameralar ve önce/sonra kayıtları bağımsız yeni kişiler değildir. Manifestteki ayrılık bu koşu için doğrulandı; tur5'in tüm eski eğitim geçmişi burada yeniden denetlenmedi.

Bu, üç kameralı MCD testi. Önceki 28 kayıtlık ana test veya 42 kişilik UBFC testiyle aynı küme değildir; o raporlardaki sayılarla doğrudan iyileşme karşılaştırması yapılmamalı. Burada UBFC, PURE veya gerçek telefon canlı kullanımı yeniden ölçülmedi. EMPD kullanılmadı.

B koşusu tur5'ten başlayıp yalnız MCD kaynak ağırlığıyla (`mcd=1`), öğrenme oranı `5e-5` ve `--phone-aug` ile devam etmiş. Tek seed sonuçları var. Aynı koşullarda artırmasız **A kontrolü henüz bu arşivde yok**. Dolayısıyla kötüleşmeyi yalnız telefon artırmasına bağlayamayız; eğitim verisinin daralması veya ince ayar ayarlarının etkileri de ayrıştırılmadı. Sonraki kontrollü adım A/B karşılaştırmasıdır; C'nin daha iyi olacağı varsayılmamalı. Test sonuçlarına bakarak ayar seçmek yerine doğrulama setiyle seçim yapılmalı ve nihai iddia yeni, dokunulmamış kişilerde doğrulanmalı.

## Aygıt ve arşiv

Bu inceleme yalnız CPU ile dosya, tablo ve ağırlık kontrolüdür; yerelde eğitim veya yeni çıkarım çalıştırılmadı, GPU kullanılmadı. İndirilen arşivin değerlendirme ayarları ise özgün Kaggle koşusu için `device: cuda` kaydediyor. Arşivdeki test sayıları bu tamamlanmış Kaggle koşusundan alınmıştır; CPU'da yeniden ölçüldükleri iddia edilmez.

`cikti/` altındaki dosyalar arşivden değiştirilmeden çıkarıldı. Arşiv SHA-256: `446bf6d01cae629e4b53bf52c1b55067c7fbefb7ec99f49b93c830cc213be514`.

- [Best karşılaştırmasının özgün raporu](cikti/karsilastirma_best/SONUCLAR.md)
- [Son checkpoint karşılaştırmasının özgün raporu](cikti/karsilastirma_last/SONUCLAR.md)
- [Deney ve kişi bölmeleri](cikti/deney.json)
