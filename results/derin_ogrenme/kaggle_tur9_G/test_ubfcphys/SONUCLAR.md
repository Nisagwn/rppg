# MMRPhys 7E'den + yeni teknikler (9. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) `results/derin_ogrenme/kaggle_tur7_E/last.pth` ağırlıklarından başlatılarak eğitildi. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_ubfcphys`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 23 test videosu

| Yöntem | UBFC-Phys aritmetik | UBFC-Phys dinlenme | UBFC-Phys konuşma | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| POS (yüz kırpıntısı) | 16.04 | 8.72 | 24.39 | 16.40 | 36.32 | 15.94 |
| POS (yüz kırpıntısı)+Viterbi | 14.43 | 7.81 | 26.95 | 16.48 | 37.85 | 15.23 |
| FactorizePhys PURE (hazır) | 20.19 | 8.14 | 28.74 | 18.98 | 37.51 | 18.18 |
| FactorizePhys PURE (hazır)+Viterbi | 22.85 | 8.21 | 26.46 | 19.01 | 37.00 | 15.84 |
| 7. tur B (MMRPhys sıfırdan) | 22.38 | 8.06 | 29.40 | 19.84 | 36.57 | 19.05 |
| 7. tur E son epoch (başlangıç) | 22.30 | 8.31 | 31.05 | 20.48 | 35.89 | 17.36 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 22.27 | 7.95 | 31.92 | 20.64 | 36.23 | 15.86 |
| 3. tur (uygulamadaki) | 23.33 | 8.64 | 31.33 | 21.00 | 35.55 | 16.89 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 21.71 | 8.18 | 33.63 | 21.15 | 37.43 | 14.41 |
| 9. tur G en iyi epoch+Viterbi | 21.96 | 8.07 | 34.08 | 21.35 | 37.17 | 14.47 |
| 7. tur E son epoch (başlangıç)+Viterbi | 21.97 | 8.22 | 33.99 | 21.37 | 37.25 | 14.62 |
| 5. tur | 23.70 | 8.68 | 32.05 | 21.38 | 35.21 | 16.71 |
| 9. tur G en iyi epoch | 23.00 | 8.69 | 33.20 | 21.57 | 35.04 | 17.93 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 22.50 | 8.40 | 34.19 | 21.66 | 36.57 | 13.86 |
| 3. tur (uygulamadaki)+Viterbi | 23.07 | 8.09 | 34.01 | 21.67 | 37.00 | 13.82 |
| 5. tur+Viterbi | 23.05 | 8.17 | 35.39 | 22.17 | 35.72 | 15.48 |

## Referans etiketi temiz test videoları (7/23)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: s20_T1 (iyi %77, SNR 2.9 dB), s20_T2 (iyi %10, SNR -2.7 dB), s20_T3 (iyi %80, SNR 2.3 dB), s25_T2 (iyi %13, SNR -1.5 dB), s25_T3 (iyi %17, SNR -0.8 dB), s30_T3 (iyi %43, SNR 0.4 dB), s35_T1 (iyi %30, SNR -1.2 dB), s35_T2 (iyi %0, SNR -2.7 dB), s35_T3 (iyi %10, SNR -1.9 dB), s45_T2 (iyi %13, SNR -1.7 dB), s45_T3 (iyi %30, SNR -1.2 dB), s50_T2 (iyi %3, SNR -2.7 dB), s50_T3 (iyi %80, SNR 4.6 dB), s55_T1 (iyi %63, SNR 1.1 dB), s55_T2 (iyi %0, SNR -2.0 dB), s55_T3 (iyi %63, SNR 3.1 dB).

| Yöntem | UBFC-Phys dinlenme | UBFC-Phys konuşma | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| 3. tur (uygulamadaki)+Viterbi | 5.91 | 13.72 | 8.14 | 49.02 | 10.75 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 5.99 | 14.81 | 8.51 | 46.78 | 10.81 |
| 9. tur G en iyi epoch+Viterbi | 5.86 | 16.13 | 8.80 | 47.06 | 10.81 |
| 7. tur E son epoch (başlangıç)+Viterbi | 6.07 | 15.89 | 8.88 | 47.06 | 10.81 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 6.37 | 15.37 | 8.94 | 45.94 | 10.80 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 6.24 | 16.35 | 9.13 | 47.06 | 10.77 |
| FactorizePhys PURE (hazır)+Viterbi | 6.20 | 16.98 | 9.28 | 46.78 | 10.74 |
| 7. tur B (MMRPhys sıfırdan) | 6.18 | 18.35 | 9.66 | 47.06 | 10.76 |
| 5. tur+Viterbi | 6.05 | 19.25 | 9.82 | 45.38 | 10.76 |
| 7. tur E son epoch (başlangıç) | 6.71 | 18.14 | 9.98 | 45.94 | 10.76 |
| 3. tur (uygulamadaki) | 6.74 | 18.50 | 10.10 | 47.62 | 10.73 |
| FactorizePhys PURE (hazır) | 6.49 | 20.00 | 10.35 | 46.78 | 10.73 |
| 5. tur | 6.94 | 19.03 | 10.40 | 45.94 | 10.74 |
| POS (yüz kırpıntısı) | 6.49 | 20.58 | 10.52 | 46.50 | 10.50 |
| 9. tur G en iyi epoch | 7.20 | 18.82 | 10.52 | 45.38 | 10.77 |
| POS (yüz kırpıntısı)+Viterbi | 5.07 | 24.50 | 10.63 | 48.18 | 6.83 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
