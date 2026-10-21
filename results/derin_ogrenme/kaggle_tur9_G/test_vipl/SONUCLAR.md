# MMRPhys 7E'den + yeni teknikler (9. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) `results/derin_ogrenme/kaggle_tur7_E/last.pth` ağırlıklarından başlatılarak eğitildi. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_vipl`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

## Eğitim verisi

- 5054 video, 863 kişi, 44.3 saat (yüz bulunma oranı <%50 olan 565 video çıkarıldı)
- MCD: 3003 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), video başına ilk 30 s
- UBFC: 34 denek
- PURE: 58 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- VIPL-HR (source1/3): 1104 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- DLCN: 628 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- COHFACE: 132 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- UBFC-Phys (bilek sensörü): 95 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.7–1.5× (HR aralığını genişletir), parlaklık ×0.8–1.2; yüz kutusu kayması ±%10; nabız dengeli örnekleme (seyrek nabız aralıkları en fazla 3×)
- Kayıp: SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır) + 0.2 × spektral KL (nabız bandı); AdamW, cosine öğrenme oranı
- Seçim: en iyi epoch doğrulama kişilerinde pencere MAE (argmax) ile; ağırlıkların EMA'sı (0.999) doğrulandı ve kaydedildi

Eğitim: 100 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 1.84 → en iyi 1.67 BPM (epoch 3).

## Ortalama MAE (BPM) — 282 test videosu

| Yöntem | VIPL (source1) | VIPL (source3) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 3.86 | 3.16 | 3.49 | 82.99 | 1.23 |
| 7. tur E son epoch (başlangıç)+Viterbi | 3.86 | 3.31 | 3.57 | 82.54 | 1.26 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 3.80 | 3.88 | 3.84 | 82.55 | 1.24 |
| 9. tur G en iyi epoch+Viterbi | 4.62 | 3.67 | 4.12 | 82.05 | 1.23 |
| FactorizePhys PURE (hazır)+Viterbi | 4.24 | 4.80 | 4.53 | 77.47 | 1.47 |
| POS (yüz kırpıntısı)+Viterbi | 5.61 | 4.10 | 4.81 | 76.07 | 1.57 |
| 7. tur B (MMRPhys sıfırdan) | 5.26 | 5.14 | 5.19 | 79.46 | 1.77 |
| 5. tur+Viterbi | 5.34 | 5.13 | 5.23 | 75.57 | 1.76 |
| 7. tur E son epoch (başlangıç) | 5.32 | 5.29 | 5.30 | 78.60 | 1.79 |
| 3. tur (uygulamadaki)+Viterbi | 5.60 | 5.25 | 5.41 | 75.14 | 1.80 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 5.38 | 5.78 | 5.59 | 78.08 | 1.84 |
| 9. tur G en iyi epoch | 5.96 | 5.96 | 5.96 | 78.28 | 2.12 |
| FactorizePhys PURE (hazır) | 6.13 | 6.41 | 6.28 | 73.53 | 3.18 |
| POS (yüz kırpıntısı) | 8.29 | 7.16 | 7.69 | 70.04 | 4.60 |
| 5. tur | 8.09 | 8.46 | 8.28 | 69.98 | 4.68 |
| 3. tur (uygulamadaki) | 8.50 | 8.32 | 8.41 | 69.67 | 5.13 |

## Referans etiketi temiz test videoları (275/282)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: p10_v3_source1 (iyi %40, SNR -0.6 dB), p10_v3_source3 (iyi %40, SNR -0.8 dB), p35_v7_source1 (iyi %76, SNR 2.2 dB), p35_v7_source3 (iyi %76, SNR 2.2 dB), p40_v3_source1 (iyi %60, SNR 4.8 dB), p40_v3_source3 (iyi %60, SNR 4.8 dB), p45_v3_source3 (iyi %66, SNR 4.2 dB).

| Yöntem | VIPL (source1) | VIPL (source3) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 3.63 | 2.98 | 3.29 | 83.66 | 1.17 |
| 7. tur E son epoch (başlangıç)+Viterbi | 3.62 | 3.09 | 3.34 | 83.22 | 1.22 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 3.57 | 3.65 | 3.61 | 83.25 | 1.20 |
| 9. tur G en iyi epoch+Viterbi | 4.41 | 3.49 | 3.92 | 82.66 | 1.19 |
| FactorizePhys PURE (hazır)+Viterbi | 3.98 | 4.60 | 4.31 | 78.23 | 1.42 |
| POS (yüz kırpıntısı)+Viterbi | 5.49 | 3.82 | 4.60 | 76.96 | 1.53 |
| 7. tur B (MMRPhys sıfırdan) | 5.03 | 4.91 | 4.97 | 80.07 | 1.59 |
| 5. tur+Viterbi | 5.12 | 4.87 | 4.99 | 76.23 | 1.67 |
| 7. tur E son epoch (başlangıç) | 5.12 | 5.02 | 5.07 | 79.24 | 1.69 |
| 3. tur (uygulamadaki)+Viterbi | 5.39 | 4.95 | 5.16 | 75.93 | 1.74 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 5.16 | 5.52 | 5.35 | 78.76 | 1.77 |
| 9. tur G en iyi epoch | 5.77 | 5.70 | 5.73 | 79.00 | 1.88 |
| FactorizePhys PURE (hazır) | 5.82 | 6.14 | 5.99 | 74.37 | 3.06 |
| POS (yüz kırpıntısı) | 8.18 | 6.54 | 7.32 | 70.85 | 4.20 |
| 5. tur | 7.88 | 8.23 | 8.07 | 70.72 | 4.29 |
| 3. tur (uygulamadaki) | 8.29 | 8.06 | 8.17 | 70.48 | 4.84 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
