# İnce Ayarlı FactorizePhys — Test Sonuçları

PURE'da ön-eğitimli FactorizePhys (rPPG-Toolbox) MCD-rPPG + UBFC-rPPG'nin **test dışı** kişileriyle ince ayarlandı ve önceki karşılaştırmanın aynı 28 videosunda (UBFC 8 denek + MCD önden webcam 20 video, 10 kişi) test edildi. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

## Eğitim verisi

- 823 video, 163 kişi, 27.4 saat (yüz bulunma oranı <%50 olan 140 video çıkarıldı)
- MCD: 820 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), ilk 120 s
- UBFC: 3 denek
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: negatif Pearson; AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi

Eğitim: 43 epoch (500 adım × 8 parça). Doğrulama MAE: ön-eğitimli 8.79 → en iyi 2.37 BPM (epoch 40).

## Ortalama MAE (BPM) — 28 test videosu

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| FactorizePhys ince ayarlı+Viterbi | 1.76 | 0.88 | 1.06 | 1.19 | 95.30 | 0.57 |
| FactorizePhys ince ayarlı (son epoch)+Viterbi | 1.65 | 1.05 | 1.10 | 1.24 | 94.99 | 0.59 |
| FactorizePhys ince ayarlı | 1.16 | 1.35 | 1.35 | 1.29 | 96.40 | 0.51 |
| FactorizePhys ince ayarlı (son epoch) | 1.18 | 1.60 | 1.29 | 1.37 | 95.93 | 0.53 |
| FactorizePhys PURE (hazır)+Viterbi | 1.42 | 2.19 | 3.88 | 2.57 | 88.94 | 1.07 |
| FactorizePhys PURE (hazır) | 1.00 | 3.42 | 4.78 | 3.21 | 88.56 | 1.33 |
| POS tüm yüz+Viterbi | 2.04 | 3.69 | 4.59 | 3.54 | 88.70 | 1.16 |
| POS ortalama+Viterbi | 1.96 | 4.09 | 7.60 | 4.73 | 85.54 | 1.38 |
| POS klasik (ortalama+argmax) | 1.68 | 5.77 | 7.87 | 5.35 | 84.18 | 2.43 |

## Video bazında (ince ayarlı + Viterbi vs POS tüm yüz + Viterbi)

- 28 videonun 14'inde fark ≤0.5 BPM, 13'inde ince ayarlı model daha iyi, 1'inde daha kötü.

En zor 5 video (POS'a göre):

| Video | POS+Viterbi | PURE hazır+Viterbi | İnce ayarlı+Viterbi |
|---|---:|---:|---:|
| 1097_FullHDwebcam_before | 23.17 | 9.10 | 2.99 |
| 1097_FullHDwebcam_after | 23.03 | 11.00 | 5.22 |
| 1107_FullHDwebcam_after | 14.53 | 19.98 | 0.61 |
| 1107_FullHDwebcam_before | 5.71 | 4.33 | 0.53 |
| subject4 | 4.87 | 3.86 | 5.00 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
