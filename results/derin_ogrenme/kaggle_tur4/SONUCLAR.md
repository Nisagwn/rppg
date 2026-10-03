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

Eğitim: 160 epoch (500 adım × 8 parça). Doğrulama MAE: ön-eğitimli 10.58 → en iyi 2.84 BPM (epoch 97).

## Ortalama MAE (BPM) — 28 test videosu

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| FactorizePhys ince ayarlı+Viterbi | 1.56 | 0.89 | 0.95 | 1.10 | 95.81 | 0.54 |
| FactorizePhys ince ayarlı (son epoch)+Viterbi | 1.56 | 0.94 | 0.94 | 1.12 | 95.56 | 0.54 |
| 3. tur (son epoch)+Viterbi | 1.70 | 0.90 | 0.90 | 1.13 | 95.50 | 0.55 |
| FactorizePhys ince ayarlı (son epoch) | 0.95 | 1.21 | 1.26 | 1.15 | 96.55 | 0.48 |
| 1. tur (başlangıç)+Viterbi | 1.81 | 0.85 | 1.02 | 1.19 | 94.91 | 0.57 |
| FactorizePhys ince ayarlı | 1.03 | 1.29 | 1.25 | 1.20 | 96.45 | 0.49 |
| 3. tur (son epoch) | 1.08 | 1.53 | 1.31 | 1.32 | 96.35 | 0.47 |
| 1. tur (başlangıç) | 1.12 | 1.53 | 1.38 | 1.36 | 95.64 | 0.53 |
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
| 1097_FullHDwebcam_before | 23.17 | 9.10 | 3.63 |
| 1097_FullHDwebcam_after | 23.03 | 11.00 | 4.47 |
| 1107_FullHDwebcam_after | 14.53 | 19.98 | 0.66 |
| 1107_FullHDwebcam_before | 5.71 | 4.33 | 0.49 |
| subject4 | 4.87 | 3.86 | 5.02 |

## Referans etiketi temiz test videoları (26/28)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: subject3 (iyi %57, SNR 1.8 dB), subject4 (iyi %39, SNR -0.4 dB).

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| 3. tur (son epoch)+Viterbi | 0.79 | 0.90 | 0.90 | 0.87 | 97.13 | 0.53 |
| FactorizePhys ince ayarlı+Viterbi | 0.89 | 0.89 | 0.95 | 0.91 | 97.01 | 0.50 |
| FactorizePhys ince ayarlı (son epoch)+Viterbi | 0.90 | 0.94 | 0.94 | 0.93 | 96.74 | 0.51 |
| 1. tur (başlangıç)+Viterbi | 0.94 | 0.85 | 1.02 | 0.94 | 96.49 | 0.56 |
| FactorizePhys ince ayarlı (son epoch) | 0.73 | 1.21 | 1.26 | 1.12 | 96.68 | 0.46 |
| FactorizePhys ince ayarlı | 0.73 | 1.29 | 1.25 | 1.14 | 96.68 | 0.46 |
| 3. tur (son epoch) | 0.70 | 1.53 | 1.31 | 1.25 | 96.68 | 0.46 |
| 1. tur (başlangıç) | 0.74 | 1.53 | 1.38 | 1.29 | 95.91 | 0.50 |
| FactorizePhys PURE (hazır)+Viterbi | 0.78 | 2.19 | 3.88 | 2.51 | 89.34 | 0.95 |
| FactorizePhys PURE (hazır) | 0.73 | 3.42 | 4.78 | 3.32 | 88.15 | 1.15 |
| POS tüm yüz+Viterbi | 1.31 | 3.69 | 4.59 | 3.49 | 89.67 | 1.12 |
| POS ortalama+Viterbi | 1.29 | 4.09 | 7.60 | 4.79 | 86.34 | 1.32 |
| POS klasik (ortalama+argmax) | 1.29 | 5.77 | 7.87 | 5.54 | 84.10 | 2.16 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
