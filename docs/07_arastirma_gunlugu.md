# Araştırma Günlüğü — Derin Öğrenme Aşaması

Bu belge, proje bittikten sonra yazılacak makalenin ham malzemesidir. Hangi deneyin neden yapıldığı, ne çıktığı,
hangi kararın alındığı ve neyin başarısız olduğu kronolojik olarak burada toplanır. Ayrıntılı tablolar ilgili
klasörlerdeki `SONUCLAR.md` dosyalarındadır; burada yalnızca özet ve kaynak gösterilir.

Son güncelleme: 17 Ekim 2026.

---

## 1. Ortak deney düzeni

Bütün turlarda aynı kalanlar:

- **Ön işleme** (rPPG-Toolbox ile aynı): Haar yüz kutusu ×1.5, 30 karede bir yeniden tespit, 72×72 kırpıntı,
  ham RGB, 30 fps'e yeniden örnekleme. Model girdisi 160 kare (5.3 s).
- **Nabız çıkarımı:** model dalgası → detrend + bant geçiren → 10 s pencere / 1 s adım → argmax ya da
  **Viterbi takibi** (projenin klasik aşamadaki katkısı).
- **Referans:** parmak PPG'sinden pencere başına spektral tepe.
- **Test kişileri hiçbir eğitimde ve doğrulamada kullanılmaz.**

| Test kümesi | İçerik | Video | Kimler gördü |
|---|---|---:|---|
| Ana test | UBFC 8 denek + MCD önden webcam (10 kişi) | 28 | – |
| Telefon/USB | Aynı 10 MCD kişisinin telefon (Iriun) ve USB kamera videoları | 28 | – |
| VIPL | VIPL-HR source1 (webcam) + source3 (Huawei P9), kişi no %5 = 0 | 283 | 7. tur B, D, E |
| DLCN | Gece / değişen ışık (10–100 lux), dinlenme + egzersiz | 152 | 7. tur D, E |
| COHFACE | Yoğun sıkıştırılmış webcam | 32 | 7. tur D, E |
| MMPD | Samsung S22, 80×60 (mini sürüm) | 120 | hiçbiri |

**Metrik:** pencere MAE (BPM), ≤5 BPM yüzdesi, medyan. Anlamlılık: video başına eşleştirilmiş Wilcoxon
(`scripts/dl_compare.py`).

---

## 2. Kronoloji

Değerler Viterbi ile ortalama MAE (BPM). "Ana" = ana test, "Tel" = telefon/USB testi.

| Tur | Tarih | Model ve başlangıç | Eğitim verisi | Ne değişti | Ana | Tel | Kaynak |
|---|---|---|---|---|---:|---:|---|
| – | – | POS (klasik, tüm yüz) | – | taban çizgisi | 3.54 | 15.63* | `tum_sonuclar.csv` |
| – | – | FactorizePhys, PURE hazır ağırlık | – | taban çizgisi | 2.57 | 7.47 | |
| yerel | 28 Eyl | FactorizePhys ← PURE | MCD 160 kişi + UBFC 3 | ilk ince ayar (RTX 3050) | 1.19 | – | `egitim/` |
| 1 | 2 Eki | FactorizePhys ← yerel e73 | MCD 590 + PURE, 200 epoch | büyük veri (Kaggle T4) | 1.17 | 1.95 | `kaggle/` |
| 2 | 2 Eki | ← 1. tur | + UBFC-Phys | kayıp 100 epoch 0.41'de düz kaldı | 1.12 | 1.90 | `kaggle_tur2/` |
| 3 | 3 Eki | ← 1. tur | aynı, **temiz etiket** | MCD yan kamera kayması düzeltildi (bulgu 3.1) | 1.13 | 1.71 | `kaggle_tur3/` |
| 4 | 3 Eki | ← PURE (taze) | temiz + telefon benzeri bozulma | kamera bazında doğrulama | 1.10 | 2.27 | `kaggle_tur4/` |
| 5 | 6 Eki | ← 3. tur | aynı (yeni veri girmedi) | – | 1.10 | 1.64 | `kaggle_tur5/` |
| 6 | 11 Eki | ← 5. tur | + MMPD, VIPL, COHFACE, DLCN | 4.6 saatte durdu; kayıp 0.36 → 0.52 yükseldi | – | – | (bulgu 3.3) |
| **7B** | 14 Eki | **MMRPhys, sıfırdan** | MCD 45 s, UBFC, PURE, VIPL (hizalı) | yeni mimari, hazır ağırlık yok, 150 epoch | **1.13** | 1.96 | `kaggle_tur7_B/` |
| 7D | 16 Eki | MMRPhys ← 7B | + DLCN, COHFACE; MCD 30 s | ince ayar, lr 2e-4, 100 epoch | 1.29 | 2.36 | `kaggle_tur7_D/` |
| 7E | 17 Eki | MMRPhys ← 7B | D ile aynı | veri seti payları sabit (MCD %70), kamera başına doğrulama; son epoch | 1.13 | 2.04 | `kaggle_tur7_E/` |
| 8F | 19 Eki | MMRPhys ← 7E son epoch | E + UBFC-Phys (model tabanlı hizalı; s17-s56: 32 kişi eğitim, 8 kişi test_ubfcphys; part1-8 zip'leri okunamadı) | UBFC-Phys %4 pay; değerlendirme last.pth | 1.05 | 2.45 | `kaggle_tur8_F/` |

\* POS'un telefon/USB değeri yüz kırpıntısı üzerinde (`test_kamera/`).
Tüm klasörler `results/derin_ogrenme/` altında. 5. tur değerleri son epoch (`last.pth`); karşılaştırmalarda bu
model kullanıldı.

**Yeni test kümelerinde (7. tur):**

| Model | VIPL | DLCN | COHFACE | MMPD |
|---|---:|---:|---:|---:|
| POS (yüz kırpıntısı) | 4.81 | – | – | 18.75 |
| FactorizePhys PURE hazır | 4.53 | – | – | 13.71 |
| 5. tur | 5.23 | 2.83 | 1.37 | 12.65 |
| 7B (MMRPhys sıfırdan) | **3.49** | 1.69 | 1.53 | 13.24 |
| 7D (7B'den ince ayar) | 4.06 | **1.31** | 1.57 | 13.17 |
| 7E (D + sabit paylar, son epoch) | 3.57 | **1.31** | 1.50 | 13.84 |
| 8F (7E + UBFC-Phys, son epoch) | 3.64 | 1.60 | 1.39 | 13.53 |

---

## 3. Bulgular (makale için katkı adayları)

### 3.1 MCD-rPPG yan kameralarında sabit etiket kayması
- Aynı oturumun üç kamerası aynı parmak sensörünü paylaşıyor; ama etiket–görüntü korelasyonunun tepesi
  önden webcam'e göre telefonda (Iriun, Wi-Fi) 4 kare, USB'de 8 kare (~270 ms, ~yarım nabız periyodu) kayık.
- USB videolarında etiket fiilen **ters işaretliydi**. 1–2. turlarda MCD verisinin ~%60'ı böyle eğitildi.
- Düzeltme sonrası telefon/USB testi 1.95 → 1.71 BPM (takipsiz argmax'ta %24). Ana testte fark yok: kayma yalnızca
  yan kameralardaydı.
- Kaynak: `results/derin_ogrenme/VERI_KALITESI.md`, `scripts/dl_common.py: CAMERA_SHIFT`.

### 3.2 MCD-rPPG parmak PPG'si UBFC/PURE'a göre ters işaretli
- Hazır modelin çıktısıyla korelasyon MCD'de ≈ −0.75, UBFC'de +0.86. Spektral nabız işarete duyarsız olduğu için
  klasik değerlendirmeler bunu göstermiyor; ama dalga düzeyinde kayıpla karışık eğitimde çelişkili hedef demek.

### 3.3 VIPL-HR'de videodan videoya değişen etiket kayması; model tabanlı hizalama
- 6. turda yeni veri geldikçe eğitim kaybı 0.36'dan 0.52'ye çıktı ve doğrulama iyileşmedi.
- POS ile ölçüm: VIPL source1/3'te kayma medyanı −12/−13 kare (referans −2), dağılım geniş. MMPD'de POS çözünürlük
  yüzünden güvenilmez.
- **Yöntem:** eğitilmiş model (5. tur) referans olarak kullanıldı. Model dalgası ile etiket ±45 kare kaydırılarak
  karşılaştırıldı (`scripts/dl_sync_check.py`). Senkronu bilinen ana test videolarında tepe tam 0 karede
  (r 0.82–0.84).
- VIPL source1/3: model–etiket nabız uyumu %81–83 (etiket doğru kişiye ait), ama kayma −27..+11 kare ve senaryoya
  bağlı (ör. source1 v1 −21, v2 −2). Bazı videolarda −34 kare.
- Etiket video başına kaydırıldıktan sonra tepe bütün videolarda 0 karede, r 0.65–0.96. Hizalı korelasyonu
  < 0.4 olan videolar çıkarıldı: source1 %80, source3 %78, DLCN %92, COHFACE %97 kaldı.
- **VIPL source2 (RealSense) kullanılamaz:** model–etiket uyumu %39, kaymalar rastgele.
- Bu, MCD bulgusunun (3.1) genelleşmiş hali: açık rPPG veri setlerinde etiket senkronu sessizce bozuk olabilir ve
  spektral değerlendirme bunu göstermez.

### 3.4 Sıfırdan eğitilen MMRPhys, ince ayarlı FactorizePhys ile ana testte eşit
- 7B: hiçbir hazır ağırlık yok; ana test 1.13 BPM, 5. tur 1.10 (**p = 0.074**, 28 videonun 24'ünde fark ≤ 0.5 BPM).
- Telefon/USB'de 7B geride: 1.96 / 1.64 (**p = 0.001**, 7 videoda daha kötü, hiçbirinde daha iyi değil).
  Olası sebep: 5. tur MCD yan kameralarını beş tur boyunca gördü; 7B'de MCD verisi eğitim sırasında geldi.
- **Eğitimde görmediği veri setlerinde genelleme:** DLCN'de 7B 1.69 / 5. tur 2.83 (**p < 0.001**, 46'ya 4 video).
  COHFACE'te 1.53 / 1.37 (p = 0.077, anlamlı değil). İki modelin de görmediği bir veri setinde MMRPhys anlamlı
  ölçüde daha iyi; ama 7B'nin VIPL'i görmüş olması da katkı yapmış olabilir (A/C deneyleri ayırırdı).

### 3.5 Veri dengesi: yeni veri eklemek eski koşulları bozabilir
- 7D: DLCN ve COHFACE eklenince DLCN testi 1.69 → 1.31 (**p < 0.001**, 16'ya 2 video).
- Telefon/USB 1.96 → 2.36 (p = 0.048, sınırda). Ana test (1.13 → 1.29, p = 0.70) ve VIPL (p = 0.61) farkları
  **anlamlı değil**.
- Sebep adayı: örnekleme kare sayısıyla orantılı; MCD 30 s'ye inip yeni veri gelince MCD'nin payı %78 → %62.
  Ayrıca doğrulamada MCD'nin 3 kamerası 6 videoyla temsil ediliyordu.
- **7E sonucu (hipotez doğrulandı):** paylar sabitlenince (gerçekleşen MCD %73) telefon/USB 2.36 → 2.04
  (D'ye göre **p = 0.013**), ana test B ile aynı (1.13; p = 0.19), DLCN kazancı korundu (B'ye göre 1.69 → 1.31,
  **p < 0.001**). Bedeli: VIPL B'ye göre 3.49 → 3.57 (**p = 0.026**). Telefon/USB'de 5. tur hâlâ en iyi (1.64,
  p = 0.001). E, tek bir modelin bütün testlerde en dengeli sonucu.

### 3.8 Küçük doğrulama kümesiyle en iyi epoch seçimi güvenilmez
- 7E'de en iyi epoch 7 seçildi (doğrulama 1.32), sonraki 93 epoch geçemedi. Ama son epoch **bütün test kümelerinde**
  daha iyi: ana test 1.27 → 1.13 (**p = 0.001**), telefon/USB 2.16 → 2.04, VIPL 3.76 → 3.57, DLCN 1.39 → 1.31.
- Sebep: grup başına 6 video; MCD önden webcam grubu epoch'tan epoch'a 2.0–4.7 BPM oynuyor ve ortalamayı belirliyor.
- Karar: E için son epoch kullanılıyor. Sonraki deneylerde son epoch ya da birkaç epoch ortalaması.

### 3.10 8F: UBFC-Phys eklemek ölçülebilir bir fark yaratmadı
- 7E son epoch'tan, UBFC-Phys (%4 pay, model tabanlı hizalı, 95 video) eklenerek 100 epoch.
- Ortalama MAE (son epoch): ana 1.05 (şimdiye kadarki en düşük), telefon/USB 2.45, VIPL 3.64, DLCN 1.60, COHFACE 1.39.
- **Hiçbir fark anlamlı değil:** F vs E ana p = 0.095, telefon/USB p = 0.61, VIPL p = 0.49, DLCN p = 0.98, COHFACE
  p = 0.08, MMPD p = 0.15. Ortalamadaki oynamalar birkaç videodan geliyor (ör. DLCN'de 5'e 1 video).
  F vs 5. tur ana p = 0.27; telefon/USB'de 5. tur hâlâ anlamlı ölçüde iyi (1.64, p < 0.001).
- **UBFC-Phys testi kullanılamaz:** bütün yöntemler ~20 BPM (POS dahil); konuşma ve aritmetik görevlerinde bilek
  sensörü referansı bozuk. Bu test kümesi sonuç tablolarına alınmamalı; yalnızca dinlenme görevi (~8 BPM) bakılabilir.
- En iyi epoch yine erken (6) ve son epoch'tan kötü (ana 1.19 / 1.05): 3.8'deki bulgu tekrarlandı.

### 3.9 Mobil uygulama gerçek veri doğrulaması (v12, 3. tur FactorizePhys)
- MCD test kişilerinin 60 kesiti (10 kişi × 3 kamera × 2 durum, 40 s) Chrome'a sahte kamera olarak verildi
  (`scripts/validate_mobile.py`, `results/mobil_dogrulama_v12/`).
- Sonuç verilen pencerelerde MAE: önden 3.24 (kapsama %81, sonuçsuz kesit 0/20), telefon 2.31 (%48, 7/20),
  USB yan 4.41 (%23, 13/20). Aynı kesitlerde Python POS hattı 6.39 / 10.34 / 17.53.
- Uygulama vs Python hattı (ikisinin de sonuç verdiği 40 kesit): 3.14 / 9.37, **p = 0.011**.
- Eski POS uygulaması vs yeni (iki doğrulamada da 30 fps olan 13 önden kesit): 8.99 → 2.45, **p = 0.013**; ama
  kapsama %97 → %81.
- Zayıf nokta: pico yüz bulucusu yan açıda ve telefon görüntüsünde yüzü kaçırıyor. Sonraki iş: yüz bulucu ve kalite
  eşiği; uygulamaya 5. tur ya da 7E modeli.

### 3.11 Mobil yüz dedektörü: pico → karma pico + YuNet (v13)
- Teşhis (saniyelik `window.__rppg.diag`): v12'de sonuçsuz 20 kesitte ölçümsüz saniyelerin %81'i yüz bulunamadığı
  için; SNR kapısı yok, kalan kayıp model penceresinin kare boşluğuyla bölünmesi (o da aralıklı yüz kaybından).
- pico parametreleri (eşik, ince tarama, döndürme, bellek) telefonu %57 → %99'a çıkarabiliyor ama USB yan açıda
  en iyi %61 (çevrimdışı, 29 kesit); yetmedi.
- YuNet (230 KB ONNX, MIT, wasm Worker) karelerin ≥ %99'unda yüz buluyor; kutusu önden karelerde öğrenilen eşlemeyle
  pico kutusuna çevriliyor. Karma: önce pico, bulamazsa YuNet (önden kamerada YuNet hiç çağrılmıyor).
- 60 kesit (`results/mobil_dogrulama_yuz/`): kapsama önden/telefon/USB 81/48/23 → 93/95/94 %, sonuçsuz kesit
  20 → 0; iki koşuda da ölçülen 40 kesitte MAE 3.14 → 2.85 (**p = 0.17**, fark yok); pencere sayısı telefon
  **p = 0.001**, USB **p = 0.0001**. Yeni kesitlerde MAE USB 3.28, telefon 6.64.

### 3.12 Uygulama içinde model karşılaştırması: 3. tur / 5. tur / 7E (v13)
- Aynı 60 kesit, her kesit üç modelle art arda (sıra döndürülerek) ölçüldü (`validate_mobile.py --models`,
  `results/mobil_dogrulama_modeller/KARSILASTIRMA.md`). Makine yüklüydü; ilk 14 kesit GPU açık, kalanı kapalı.
- MAE (kesit ortalaması) / kapsama: tur3 4.17 / %53, tur5 4.35 / %52, 7E 3.98 / %52; medyan 2.24 / 2.42 / 2.09.
  Üçünün de ölçtüğü 36 kesitte Friedman **p = 0.56**; ikili Wilcoxon'ların hiçbiri anlamlı değil (en küçük: önden
  webcam tur5 vs 7E, p = 0.081). Aynı 3. tur modelinin v12 koşusuyla farkı da anlamlı değil (p = 0.69).
- **Olumsuz sonuç:** gerçek zamanlı tarayıcı doğrulaması ±0.3 BPM'lik model farklarını ayıramıyor; tekrar gürültüsü
  (aynı kesit ve modelde 1.3 / 2.4 BPM, ara sıra takibin yanlış tepeye kilitlenmesi) model farkından büyük.
- Tarayıcıda çıkarım medyanı: 509 / 584 / 409 ms (tur3 ve tur5 aynı mimari: aradaki fark yük gürültüsü).
- Ajanın önerisi 7E idi (çevrimdışı DLCN/VIPL çok daha iyi, dosya 163 KB, çıkarım daha hızlı). **Karar (19 Eki):
  uygulamaya 5. tur FactorizePhys** (v14): uygulama içinde fark yok; çevrimdışı telefon/USB testinde 5. tur anlamlı
  ölçüde iyi (1.64 / 2.04, p = 0.001) ve telefon kamerası uygulamanın asıl kullanımı; MMRPhys lisansı yalnızca
  araştırma amaçlı kullanıma izin verdiği için herkese açık uygulamada FactorizePhys daha güvenli.
- Bu koşu pico'lu (v12/v13 öncesi) yüz dedektörüyle yapıldı; kapsama ~%52. Karma dedektörle (3.11) yeniden
  ölçülmedi.

### 3.6 Viterbi takibi derin öğrenme çıktısında da büyük kazanç sağlıyor
- Klasik aşamanın katkısı derin modellerde de çalışıyor: 7B telefon/USB'de argmax 3.80 → Viterbi 1.96 BPM
  (**p < 0.001**, 15'e 1 video). Bütün modellerde ve test kümelerinde benzer.

### 3.7 Veri setlerine özgü notlar
- **MMPD mini (80×60):** bütün modeller ~13 BPM. İşaret doğru, kayma ~−5 kare; sorun çözünürlük.
- **COHFACE:** POS uyumu düşük (%45), ama 5. tur modeli 1.0 BPM. Sıkıştırma klasik yöntemi bozuyor, derin modeli
  daha az.
- **DLCN:** etiket iyi (SNR 8.4 dB, POS uyumu %73), 780 videonun 752'sinde işaret +.

### 3.13 Test zamanı artırma ve model birleşimi yeniden eğitimsiz kazanç vermedi (uygulama için)
- `scripts/dl_ensemble.py`, CPU'da, ana test (28) ve telefon/USB (28); `results/derin_ogrenme/birlesim/`.
  TTA: %50 örtüşmeli parçalar + yatay çevirme ortalaması. Birleşim: modellerin standartlaştırılmış dalgalarının ortalaması.
- 5. tur TTA: ana test 1.10 → 1.03 (**p < 0.001**, ama yalnızca 2 videoda > 0.5 BPM fark); telefon/USB 1.64 → 1.67
  (p = 0.10). 7E'de TTA ana testi kötüleştirdi (1.13 → 1.20, p = 0.010). 8F'de telefon/USB 2.45 → 2.10.
- Birleşimler 5. turu hiçbir testte geçmedi; 5. tur + 7E telefon/USB'de kötü (1.82 / 1.64, **p = 0.003**).
- Karar: uygulamaya eklenmez (telefon/USB'de kazanç yok, çıkarım süresi ~2 kat). TTA ana testte "küçük ama tutarlı"
  bir kazanç olarak raporlanabilir.

### 3.14 Uygulamadaki hata takipçiden gelmiyor
- `scripts/dl_tracker_sim.py`: uygulamanın çevrimiçi takipçisi 5. tur dalgasında (ana test) 1.25 BPM, bütün videoda
  Viterbi 1.10. Takipçiye sıçrama payı (0.005–0.05) fark yaratmadı (1.23–1.27); varsayılan 0 kaldı.
- 20/30 s'lik "tek seferlik ölçüm" (klip başına Viterbi medyanı) ~1.3 BPM: algoritma kazancı yok.
- Uygulamadaki 3–4 BPM ile çevrimdışı 1.1–1.6 arasındaki fark model girdisinden (kırpma farkı, kare kaybı) gelmeli:
  9. tur G'deki yüz kutusu kayması artırması bunu hedefliyor.

### 3.15 Standart protokol (PURE → UBFC-rPPG): sıfırdan MMRPhys hazır FactorizePhys'e çok yakın
- 9. tur S1: MMRPhys **sıfırdan**, yalnızca PURE ile 30 epoch; UBFC-rPPG'nin **42 kişisinin hepsinde** test
  (`results/derin_ogrenme/kaggle_tur9_S1/`).
- 10 s pencere MAE: **0.74 BPM** (Viterbi 0.83), ≤5 BPM %98.5. rPPG-Toolbox'un PURE'da eğitilmiş resmî FactorizePhys
  ağırlıkları aynı ölçümde 0.68 (Viterbi 0.82). Fark küçük ama anlamlı (0.74 / 0.68, **p = 0.007**; 42 videonun
  3'ünde biri, 3'ünde öbürü > 0.5 BPM iyi). POS 1.86 (p < 0.001).
- Referansı temiz 40 videoda: MMRPhys 0.68, FactorizePhys hazır 0.62.
- Yorum: hiç hazır ağırlık kullanmadan, aynı protokolde yayımlanmış modelin resmî ağırlıklarına 0.06 BPM yaklaşıldı.
  Literatürdeki tablolar çoğunlukla video düzeyinde (bütün videonun spektrumu) MAE verir; bizim metrik 10 s pencere,
  daha zor. Doğrudan rakam karşılaştırması için aynı metrik gerekir (bkz. 5).
- Bu protokolde Viterbi kazanç vermedi (UBFC temiz, hareketsiz; takip ancak hatalı pencerelerde işe yarıyor).
- **Ama genelleme zayıf:** aynı S1 modeli ana testte (UBFC 8 + MCD önden 20) 12.1 BPM (Viterbi), hazır FactorizePhys
  2.57; MCD dinlenme 10.7, egzersiz 22.0. Yalnızca PURE'un ~1 saatlik verisiyle sıfırdan eğitilen MMRPhys UBFC'ye
  (PURE'a benzer, laboratuvar, sabit ışık) iyi aktarılıyor, MCD'ye aktarılamıyor; hazır FactorizePhys aynı veriyle
  eğitildiği hâlde daha sağlam. Bizim asıl modellerimizin (7B/7E) iyi sonucu büyük ölçüde çok kaynaklı veriden geliyor.
  Makalede iki tablo birlikte verilmeli: standart protokol (karşılaştırma) + çapraz veri seti (genelleme).
- Video düzeyi MAE artık `dl_evaluate.py`'de (`test_ozet_video.csv`); S1'in UBFC-42 için video düzeyi değeri bir
  sonraki değerlendirmede çıkacak.

### 3.16 9. tur G: yeni eğitim teknikleri birlikte kazanç vermedi (olumsuz sonuç)
- 7E son epoch'tan 100 epoch; spektral kayıp 0.2, EMA 0.999, nabız dengeli örnekleme 3×, hız 0.7–1.5×, yüz kutusu
  kayması ±%10 (`results/derin_ogrenme/kaggle_tur9_G/`).
- Pencere MAE (Viterbi), G / 7E: ana 1.29 / 1.13 (p = 0.074), telefon/USB 2.27 / 2.04 (p = 0.78), VIPL 3.84 / 3.57
  (p = 0.37), DLCN 1.45 / 1.31 (p = 0.82), COHFACE 1.54 / 1.50, MMPD 12.77 / 13.84 (p = 0.24). **Hiçbiri anlamlı değil**;
  telefon/USB'de 5. tur hâlâ anlamlı ölçüde iyi (1.64, p < 0.001).
- Video düzeyi MAE (yeni ölçüm), G / 7E / 5. tur: ana 0.50 / 0.67 / 0.62, telefon/USB 0.75 / 1.21 / 0.71, VIPL 3.47 / 3.00 /
  6.12 (G-7E p = 0.021, G kötü), DLCN 1.64 / 1.74 / 2.62. Ana ve telefon/USB farkları anlamlı değil (p > 0.4).
- Yorum: eğitim tarafındaki iyileştirmeler doygunlukta; mevcut veriyle pencere hatası ~1.1 (ana) ve ~1.6–2.0 BPM
  (telefon/USB) civarında kalıyor. Kutu kaymasının uygulama içi etkisi bu testlerde görülemez (çevrimdışı kırpıntılar
  Haar kutusundan); uygulama içi ölçüm ±0.3 BPM'yi ayıramıyordu (3.12). Kalan en büyük kaldıraç gerçek telefon verisi
  (`docs/08_veri_toplama_yol_haritasi.md`).
- **Video düzeyi rakamlar literatür tablolarıyla aynı tür:** ana test 0.50–0.67, telefon/USB 0.71–0.75, DLCN 1.64, VIPL
  3.0 BPM (bizim modeller); hazır FactorizePhys (PURE) aynı testlerde 1.39 / 7.34 / 4.69 / 4.12.

---

### 3.17 Solunum hızı model dalgasından tahmin edilemedi (olumsuz sonuç, uygulamaya eklenmedi)

`scripts/resp_experiment.py`, `results/solunum/`. MCD-rPPG'nin klinik solunum sayımı (`db.csv` "respiratory",
kayıt başına tek değer, 16–22 nefes/dk) 48 test videosunda (10 kişi × önden/telefon/USB × dinlenme/egzersiz) 5. tur
model dalgasından üç klasik modülasyonla (Karlen vd. 2013) ve kırpıntının yeşil kanalından tahmin edildi:

| Yöntem | MAE (nefes/dk) | ±3 içinde | r |
|---|---|---|---|
| RIIV (taban çizgisi) | 5.43 | %38 | 0.07 |
| RIAV (genlik) | 7.00 | %15 | −0.06 |
| RIFV (atım aralığı) | 8.04 | %17 | −0.10 |
| füzyon (medyan) | 6.56 | %19 | 0.04 |
| yeşil kanal (kırpıntı) | 9.13 | %6 | 0.13 |
| **herkese sabit 18** | **0.88** | **%96** | — |

Hiçbir yöntem sabit tahmini geçemedi, korelasyonlar sıfıra yakın. **Yorum:** (1) model nabız dalgasını üretmeye
eğitildiği için (Pearson kaybı, 0.7–3 Hz) solunum bileşenleri büyük ölçüde bastırılmış olabilir; (2) referans
kayıt sırasında senkron bir solunum sinyali değil, tek bir klinik sayım ve aralığı çok dar (sabit tahmin bu yüzden
güçlü). Doğrulanamayan bir sayı kullanıcıya gösterilmemeli: solunum uygulamaya eklenmedi. Kesin hüküm için senkron
solunum sinyali gerekir: COHFACE'in HDF5 dosyalarında göğüs kemeri solunum sinyali var (zaten eğitim verisinde
kullanılan veri seti); bir sonraki adım bu sinyalle hem bu yöntemleri hem MMRPhys'in solunum çıkışını denemek.

### 3.18 Uygulamanın yüz kutusu (YuNet/pico) modelin hatasını anlamlı artırmıyor

Soru: uygulamadaki hatanın (3.9, 3.12) kaynağı, modelin eğitimde gördüğü Haar kutusuyla telefonda gördüğü kutunun
farkı mı? `dl_prepare.py --detector app` (`AppCropper`: `mobile/app.js`'in birebir Python eşi; 480 px çalışma
karesi, 256 px YuNet, 4 karede bir tespit, YuNet→pico eşlemesi, 0.3 yumuşatma, x1.5 kare kutu, 1 s sabit tutma) ile
60 MCD test videosu (10 kişi × 3 kamera × 2 durum) uygulama kutusuyla yeniden hazırlandı (`data/dl/test_app`), aynı
videoların Haar kırpıntılarıyla karşılaştırıldı. `results/kirpma_farki/`.

**Geometri** (`scripts/crop_compare.py`, 60 karede bir, Haar kutusuna göre): önden webcam'de kutular neredeyse aynı
(merkez farkı %0/−%1, boyut 1.01, IoU medyan 0.89); telefonda yatay −%8 kayma, boyut 1.06, IoU 0.78; USB (yan) IoU
medyan 0.80 ama p10 0.21 (Haar yan yüzde yanlış/eksik buluyor).

**Model hatası** (pencere MAE, Viterbi; video başına eşleştirilmiş Wilcoxon, 48 eşleşen video):

| Yöntem | Haar | Uygulama kutusu | p |
|---|---|---|---|
| 5. tur (uygulamadaki model) | 1.32 | 1.47 | 0.67 |
| — önden / telefon / USB | 0.86 / 1.59 / 1.76 | 0.99 / 2.14 / 1.12 | 0.23 / 0.18 / 0.20 |
| FactorizePhys PURE (hazır) | 5.62 | **4.37** | **0.012** |
| POS (kırpıntı ortası) | 11.59 | **10.05** | **0.006** |

**Yorum:** (1) Kutu farkı 5. turun hatasını anlamlı artırmıyor (video düzeyinde de: 0.68 → 0.90, p=0.35); uygulama ile
çevrimdışı arasındaki fark başka yerden geliyor: canlı kameradaki kare düşmeleri ve zamanlama, yavaş telefonda
model pencerelerinin atlanması (3.14; v15–v17'de çok iş parçacığı ve hızlı ölçümle ele alındı). (2) Eğitimden bağımsız
yöntemler (hazır model, POS) uygulama kutusunda anlamlı daha iyi: YuNet kutusu daha iyi bir kırpıntı. 5. turun buna
rağmen kazanmaması, Haar kutusuna uyum sağladığını düşündürüyor. (3) Kapsam: Haar yan kamerada 20 videonun 11'inde
yüzü yarıdan az karede buldu (test dışı kaldı); uygulama kutusu 20'sinin hepsinde. Haar'la hazırlanan eğitim
verisi de aynı nedenle yan açılı videoları kaybediyor. **Sonuç:** uygulama kutusuyla yeniden eğitim olası ama küçük
bir kazanç (yan açı kapsamı, daha iyi kırpıntı) için uzun bir CPU hazırlığı + GPU turu ister; öncelik kendi telefon
verisinde (3.19).

### 3.19 Uygulama v18: veri kaydı, WebGPU seçimi, yönlendirme, geçmiş

- **Veri kaydı (60 s):** hızlı ölçümün 60 s'lik hâli; modelin gördüğü 72×72 kırpıntılar, kutular, zaman damgaları ve
  kullanıcının girdiği oksimetre değeri tek dosyada (`.rppgrec`, 60 s ≈ 25 MB). `scripts/import_own.py` 30 fps
  `dl_prepare` biçimine çevirir. Tek oksimetre değeriyle dalganın zamanlaması bilinmediğinden (Pearson kaybı fazı
  ister) bu kayıtlar **telefon test kümesi** olur (`label=sabit_nabiz`, `dl_train` atlar); oksimetre dalga kaydı
  (`--ppg`) ile eğitime girer. Uçtan uca denendi (sahte kamera, 61 s'de 1610 kare, 26 fps; içe aktarma, test:
  `tests/test_own_data.py`). Kendi verinin uygulamanın tam girdisiyle toplanması 3.18'deki kutu sorununu da kendiliğinden
  ortadan kaldırır.
- **WebGPU:** onnxruntime-web 1.30.0 WebGPU paketi; FactorizePhys'in bütün katmanları destekleniyor, çıktı wasm ile aynı
  (aynı gürültülü girdide korelasyon 0.99999999, en büyük fark 0.0006; `mobile/test/webgpu_check.mjs`). Hız cihaza göre
  değiştiğinden ilk açılışta iki arka uç aynı denemeyle ölçülür, WebGPU ≥1.5 kat hızlıysa seçilir ve hatırlanır;
  teşhis dosyasında `ep`, `ep_bench`. Ders: deneme girdisi sabit (her piksel 128) olunca kare farkları sıfır, model içinde
  denormal sayılar oluşuyor ve wasm 50 kat yavaşlıyordu (12.5 s); gürültülü girdiyle 149 ms.
- **int8 nicemleme yapılmadı:** model dosyası 0.25 MB (14 MB olan, ONNX Runtime'ın kendisi); süre ağırlıklarda değil
  160×72×72'lik etkinliklerde.
- **Yönlendirme:** yüz kutusu kısa kenarın %18'inden küçükse "yaklaştırın", %80'inden büyükse "uzaklaştırın", model
  kutusu kareden taşıyorsa "ortalayın", ışık yetersiz/çok parlak. Sinyal iyiyken gösterilmez.
- **Ölçüm geçmişi:** son 50 ölçüm, oksimetre değeri ve farkıyla, yalnızca tarayıcıda.
- Gerileme yok: aynı videoda canlı ölçüm v17 72.2 / v18 71.1 BPM, hızlı ölçüm 68.1 (videonun nabzı 66–72 arasında oynuyor).

## 4. Olumsuz sonuçlar ve mühendislik dersleri

- **2. tur (UBFC-Phys):** bilek sensörünün senkronu kişiden kişiye değişiyor; video başına hizalama gerekti. 8. turda POS
  yerine 5. tur modeliyle hizalanıyor (konuşma/aritmetikte POS |r| ~0.1, hizalamaya yetmiyordu). 18 Eki hazırlaması:
  konuşma/aritmetikte bilek sinyalinin kendisi bozuk (iyi pencere medyan %20-30, SNR < 0 dB; dinlenmede %100, 5.9 dB).
- **Yeni veri seti taraması (18 Eki):** açık ve eğitime hazır yeni gerçek veri bulunamadı. PhysDrive (HF WeiQian98,
  elle onay), RLAP ve iBVP (imzalı sözleşme) erişim bekliyor; SCAMPS açık ama sentetik (600 GB); 4TU açık ama ECG.
- **6. tur ve 7B'nin ilk iki oturumu Kaggle'da iz bırakmadan durdu** ("Read-only file system", başarısız sürüm
  çıktıyı saklamıyor). RAM sorunu değildi (izleme: 30/34 GB boş). Ortak nokta: 43 GB'lık DLCN Kaggle girdisinin
  okunması + oturumun ~90–100 GB veri yazması. DLCN'siz ~92 GB'lık oturum bitti. Çözüm: büyük girdiler GPU'suz
  hazırlama oturumunda işlenip Hugging Face'e konuyor; eğitim oturumu yalnızca hazır veriyi indiriyor.
- **Doğrulama kümesi her epoch değişince** aynı model 1.4–4.3 BPM arasında ölçüldü; en iyi epoch seçimi gürültülü.
  Çözüm: önceki seçim korunur.
- **Hugging Face anahtarı "Refresh" edilince** eski değer anında geçersiz oluyor; Kaggle'daki secret eski kaldığı için
  COHFACE "erişim yok" sanıldı. Ayrıca gated veri setlerinin dosya listesi anahtarsız istenince Kaggle'ın ortak
  IP'lerinden boş dönebiliyor.
- **Colab ücretsiz katmanı** uzun eğitimde sürekli koptu; eğitime hiç ulaşılamadı.
- **Mobil doğrulama betiği bütün videoları 30 fps sayıyordu.** MCD'nin telefon videolarının çoğu ve önden webcam
  videolarının bir kısmı 24 fps; zaman 1.25 kat hızlanınca HR şişti (telefonda MAE 17–26 BPM göründü). Kareler
  artık zaman damgalarıyla 30 fps'e taşınıyor. Eski POS dönemi doğrulamasındaki (`results/mobil_dogrulama/`) 24 fps
  MCD kesitleri de bu hatadan etkilenmişti; UBFC (30 fps) etkilenmedi. Eğitim verisi (`dl_prepare.py`) zaten zaman
  damgasıyla yeniden örnekliyordu.
- **Kaggle'da E'nin raporu yazılamadı:** başlangıç ağırlığı verilen MMRPhys için kayıp metni tanımsızdı
  (`UnboundLocalError`); test sonuçları tamamdı, rapor elle yazıldı, betik düzeltildi.
- **Hazır MMRPhys ağırlıkları** yayımlanan kodla birebir uyuşmuyor (eksik/fazla katman); zaten sıfırdan eğitildi.

---

## 5. Makaleden önce yapılması gerekenler

- [x] **7E sonucu** (3.5, 3.8). [x] Uygulamadaki model: 5. tur (3.12).
- [x] **Mobil kapsama:** yan açı ve telefon görüntüsünde yüz bulunamıyordu (3.9); karma pico + YuNet ile çözüldü (3.10).
- [ ] **A ve C deneyleri** (FactorizePhys yeni veriyle; FactorizePhys sıfırdan): "kazanç mimariden mi veriden mi"
      ve "ön-eğitim gerekli mi" sorularını kesinleştirir. Şu an 3.4'teki genelleme iddiası bunlar olmadan zayıf.
- [~] **Tekrar (seed) sayısı:** `dl_train.py --seed` eklendi (0 = önceki turlar gibi); henüz koşulmadı. Her deney tek çalıştırma. En azından ana modeli 2–3 farklı tohumla eğitip ±
      aralık vermek.
- [~] **Literatürle karşılaştırılabilir protokol:** PURE → UBFC yapıldı (3.15); video düzeyi MAE ve UBFC → PURE (S2) kaldı. standart çapraz veri seti tabloları (ör. PURE → UBFC,
      UBFC → PURE) en azından ana model için. Şu anki test kümeleri bizim tanımımız.
- [ ] **Bland-Altman** ve Pearson r tabloları (ana model, her test kümesi).
- [~] **Telefonda hız ölçümü** (MMRPhys ONNX 163 KB; masaüstü işlemcide 160 kare 0.13 s). v18 teşhis dosyası arka uç ve süreyi (`ep_bench`, `model_ms`) kaydediyor; telefonlardan toplanacak.
- [ ] **Etiket senkronu bulgusu** (3.1 + 3.3) tek başına kısa bir makale/bildiri olabilir: açık veri setlerinde
      kayma ölçümü, model tabanlı hizalama yöntemi ve eğitime etkisi.

---

## 6. Dosya haritası

| Ne | Nerede |
|---|---|
| Tur sonuçları | `results/derin_ogrenme/<tur>/SONUCLAR.md`, `test_*/` alt klasörleri |
| Etiket kalitesi (MCD, UBFC-Phys) | `results/derin_ogrenme/VERI_KALITESI.md` |
| Model tabanlı senkron analizi | `results/derin_ogrenme/senkron_model.csv`, `scripts/dl_sync_check.py` |
| Hizalama kuralları ve kaymalar | `scripts/dl_common.py` (`CAMERA_SHIFT`, `MODEL_SYNC`, `DROP_*`) |
| Eğitim / değerlendirme | `scripts/dl_train.py`, `scripts/dl_evaluate.py`, `scripts/dl_compare.py` |
| Kırpma farkı (Haar / uygulama) | `results/kirpma_farki/`, `scripts/crop_compare.py`, `dl_prepare.py --detector app` |
| Solunum denemesi | `results/solunum/`, `scripts/resp_experiment.py` |
| Telefon veri kaydı | `scripts/import_own.py` (`.rppgrec`) |
| Kaggle defterleri | `kaggle/rppg_hazirla.ipynb` (veri), `kaggle/rppg_egitim_7.ipynb` (eğitim) |
| İş planı | `docs/04_is_plani.md` |
| Kronoloji (ayrıntı) | `git log` (her commit mesajı sonuçları içeriyor) |
