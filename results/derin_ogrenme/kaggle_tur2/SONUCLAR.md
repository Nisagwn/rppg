# İnce Ayarlı FactorizePhys — Test Sonuçları

PURE'da ön-eğitimli FactorizePhys (rPPG-Toolbox) MCD-rPPG + UBFC-rPPG'nin **test dışı** kişileriyle ince ayarlandı ve önceki karşılaştırmanın aynı 28 videosunda (UBFC 8 denek + MCD önden webcam 20 video, 10 kişi) test edildi. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

## Eğitim verisi

- 3098 video, 634 kişi, 39.4 saat (yüz bulunma oranı <%50 olan 535 video çıkarıldı)
- MCD: 3006 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), ilk 45 s (disk için; kişi çeşitliliği süreden önemli)
- UBFC: 34 denek
- PURE: 58 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: negatif Pearson; AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi

Eğitim: 100 epoch (500 adım × 8 parça). Doğrulama MAE: ön-eğitimli 2.13 → en iyi 2.10 BPM (epoch 5).

## Ortalama MAE (BPM) — 28 test videosu

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| FactorizePhys ince ayarlı (son epoch)+Viterbi | 1.63 | 0.84 | 0.98 | 1.12 | 95.54 | 0.57 |
| FactorizePhys ince ayarlı+Viterbi | 1.81 | 0.78 | 0.99 | 1.15 | 95.20 | 0.58 |
| FactorizePhys ince ayarlı | 1.12 | 1.42 | 1.45 | 1.35 | 96.08 | 0.50 |
| FactorizePhys ince ayarlı (son epoch) | 1.11 | 1.37 | 1.52 | 1.35 | 96.12 | 0.52 |
| FactorizePhys PURE (hazır)+Viterbi | 1.42 | 2.19 | 3.88 | 2.57 | 88.94 | 1.07 |
| FactorizePhys PURE (hazır) | 1.00 | 3.42 | 4.78 | 3.21 | 88.56 | 1.33 |
| POS tüm yüz+Viterbi | 2.04 | 3.69 | 4.59 | 3.54 | 88.70 | 1.16 |
| POS ortalama+Viterbi | 1.96 | 4.09 | 7.60 | 4.73 | 85.54 | 1.38 |
| POS klasik (ortalama+argmax) | 1.68 | 5.77 | 7.87 | 5.35 | 84.18 | 2.43 |

## Video bazında (ince ayarlı + Viterbi vs POS tüm yüz + Viterbi)

- 28 videonun 12'inde fark ≤0.5 BPM, 15'inde ince ayarlı model daha iyi, 1'inde daha kötü.

En zor 5 video (POS'a göre):

| Video | POS+Viterbi | PURE hazır+Viterbi | İnce ayarlı+Viterbi |
|---|---:|---:|---:|
| 1097_FullHDwebcam_before | 23.17 | 9.10 | 2.83 |
| 1097_FullHDwebcam_after | 23.03 | 11.00 | 4.68 |
| 1107_FullHDwebcam_after | 14.53 | 19.98 | 0.62 |
| 1107_FullHDwebcam_before | 5.71 | 4.33 | 0.55 |
| subject4 | 4.87 | 3.86 | 4.98 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
