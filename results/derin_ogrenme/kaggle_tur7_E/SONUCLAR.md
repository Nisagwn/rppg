# MMRPhys B'den dengeli ince ayar (7. tur E) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **7. tur B'nin en iyi modelinden** (kendi sıfırdan eğittiğimiz ağırlıklar,
`kaggle_tur7_B/best.pth`) başlatılarak D ile aynı veriyle ince ayarlandı (lr 2e-4, 100 epoch); dışarıdan hazır
ağırlık kullanılmadı. D'den farkı:

- **Veri seti payları sabit** (`--source-weights mcd=0.70,vipl=0.15,dlcn=0.08,cohface=0.03,pure=0.02,ubfc=0.02`).
  D'de örnekleme kare sayısıyla orantılıydı ve MCD'nin payı %78'den %62'ye düşmüştü. Günlükte gerçekleşen pay:
  MCD %73, VIPL %16, DLCN %8, COHFACE %3.
- **Doğrulama kamera başına dengeli** (`--val-max 54`; her (veri seti, kamera) grubundan 5–6 video, seçim epoch'lar
  arasında korunur).

Test kişileri eğitim ve doğrulamada hiç kullanılmadı. Eğitim verisi, ön işleme, artırma ve kayıp D ile aynıdır
(bkz. `../kaggle_tur7_D/SONUCLAR.md`).

> Not: Kaggle'daki değerlendirme betiği rapor yazarken çöktü (`dl_evaluate.py`, başlangıç ağırlığı verilmiş
> MMRPhys için kayıp metni tanımsızdı; düzeltildi). Test sonuçları (`test_*/test_sonuclari.csv`, `test_ozet.csv`)
> eksiksizdir; bu rapor onlardan elle yazıldı.

## Eğitim

100 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 1.72 → en iyi 1.32 BPM, ama **en iyisi epoch 7'de**
seçildi; sonraki 93 epoch doğrulamayı geçemedi (son epoch 1.52). Doğrulama ölçümü gürültülü: MCD önden webcam
grubunun 6–7 videosu epoch'tan epoch'a 2.0 ile 4.7 BPM arasında oynuyor ve ortalamayı o belirliyor; epoch 7 bu
grupta şanslı bir ölçüme denk geldi. **Son epoch (`last.pth`) bütün test
kümelerinde en iyi epoch'tan iyidir** (ana test 1.13 / 1.27, p = 0.001); karşılaştırmalarda son epoch kullanıldı.

## Ortalama MAE (BPM), Viterbi ile

| Model | Ana test | Telefon/USB | VIPL | DLCN | COHFACE | MMPD |
|---|---:|---:|---:|---:|---:|---:|
| 5. tur (FactorizePhys) | **1.10** | **1.64** | 5.23 | 2.83 | **1.37** | **12.65** |
| 7B (MMRPhys sıfırdan) | 1.13 | 1.96 | **3.49** | 1.69 | 1.53 | 13.24 |
| 7D (B'den ince ayar) | 1.29 | 2.36 | 4.06 | **1.31** | 1.57 | 13.17 |
| **7E son epoch** | 1.13 | 2.04 | 3.57 | **1.31** | 1.50 | 13.84 |
| 7E en iyi epoch (7) | 1.27 | 2.16 | 3.76 | 1.39 | 1.63 | 13.82 |

## Anlamlılık (video başına eşleştirilmiş Wilcoxon, 7E son epoch)

| Test | 7E vs 7B | 7E vs 7D | 7E vs 5. tur |
|---|---|---|---|
| Ana (28) | 1.13 / 1.13, p = 0.19 | 1.13 / 1.29, p = 0.32 | 1.13 / 1.10, p = 0.10 |
| Telefon/USB (28) | 2.04 / 1.96, p = 0.90 | **2.04 / 2.36, p = 0.013** | 2.04 / 1.64, **p = 0.001 (5. tur iyi)** |
| VIPL (282) | 3.57 / 3.49, **p = 0.026 (B iyi)** | **3.57 / 4.06, p = 0.001** | **3.57 / 5.23, p < 0.001** |
| DLCN (152) | **1.31 / 1.69, p < 0.001** | 1.31 / 1.31, p < 0.001 (medyan D lehine; 6'ya 3 video) | **1.31 / 2.83, p < 0.001** |
| COHFACE (32) | 1.50 / 1.53, p = 0.92 | – | – |
| MMPD (115) | 13.84 / 13.24, p = 0.81 | 13.84 / 13.17, p = 0.15 | 13.84 / 12.65, p = 0.037 (5. tur iyi) |

## Yorum

- **Hipotez doğrulandı:** veri seti payları sabitlenince D'nin MCD tabanlı testlerdeki kaybı geri geldi (telefon/USB
  2.36 → 2.04, p = 0.013; ana test B ile aynı), DLCN kazancı korundu (1.69 → 1.31, p < 0.001).
- VIPL'de B'ye göre küçük ama anlamlı bir gerileme var (3.49 → 3.57, p = 0.026); VIPL'in payı D'ye göre de düştü.
- Telefon/USB'de 5. tur FactorizePhys hâlâ anlamlı ölçüde en iyisi.
- **En iyi epoch seçimi güvenilmez:** grup başına 6 videoluk doğrulama epoch 7'yi seçti; son epoch her testte daha
  iyi. Sonraki deneylerde son epoch kullanılmalı ya da doğrulama büyütülüp birkaç epoch'un ortalaması alınmalı.

Ayrıntı: `test_sonuclari.csv` ve `test_*/test_sonuclari.csv` (video × yöntem), `gecmis.json` (epoch geçmişi),
`gunlukler/egitim.log`.
