# MMRPhys 7E'den + UBFC-Phys (8. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) `results/derin_ogrenme/kaggle_tur7_E/last.pth` ağırlıklarından başlatılarak eğitildi. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_mmpd`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır); AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi

Eğitim: 100 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 1.84 → en iyi 1.56 BPM (epoch 6).

## Ortalama MAE (BPM) — 115 test videosu

| Yöntem | MMPD (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 12.65 | 12.65 | 56.77 | 6.74 |
| 3. tur (uygulamadaki)+Viterbi | 13.23 | 13.23 | 56.66 | 6.88 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 13.24 | 13.24 | 56.10 | 6.64 |
| 8. tur F en iyi epoch+Viterbi | 13.26 | 13.26 | 56.38 | 7.28 |
| MMRPhys 7E'den + UBFC-Phys (8. tur)+Viterbi | 13.53 | 13.53 | 55.57 | 7.17 |
| FactorizePhys PURE (hazır)+Viterbi | 13.71 | 13.71 | 55.18 | 6.56 |
| 7. tur E son epoch (başlangıç)+Viterbi | 13.84 | 13.84 | 55.30 | 7.30 |
| MMRPhys 7E'den + UBFC-Phys (8. tur) | 15.30 | 15.30 | 51.74 | 12.39 |
| 7. tur B (MMRPhys sıfırdan) | 15.48 | 15.48 | 50.89 | 12.86 |
| 7. tur E son epoch (başlangıç) | 15.66 | 15.66 | 51.08 | 13.70 |
| 8. tur F en iyi epoch | 15.66 | 15.66 | 50.77 | 14.01 |
| FactorizePhys PURE (hazır) | 16.38 | 16.38 | 48.33 | 12.81 |
| 5. tur | 16.85 | 16.85 | 49.29 | 14.28 |
| 3. tur (uygulamadaki) | 16.96 | 16.96 | 48.83 | 14.63 |
| POS (yüz kırpıntısı)+Viterbi | 18.75 | 18.75 | 40.38 | 14.52 |
| POS (yüz kırpıntısı) | 20.66 | 20.66 | 36.21 | 17.75 |

## Referans etiketi temiz test videoları (110/115)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: p10_16 (iyi %40, SNR 0.4 dB), p15_11 (iyi %17, SNR -1.8 dB), p15_15 (iyi %70, SNR 1.7 dB), p15_7 (iyi %70, SNR 0.6 dB), p5_19 (iyi %0, SNR -2.0 dB).

| Yöntem | MMPD (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 11.48 | 11.48 | 59.07 | 6.23 |
| 3. tur (uygulamadaki)+Viterbi | 11.87 | 11.87 | 58.87 | 6.55 |
| 8. tur F en iyi epoch+Viterbi | 12.27 | 12.27 | 58.33 | 5.87 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 12.27 | 12.27 | 58.13 | 6.16 |
| MMRPhys 7E'den + UBFC-Phys (8. tur)+Viterbi | 12.53 | 12.53 | 57.38 | 6.87 |
| 7. tur E son epoch (başlangıç)+Viterbi | 12.75 | 12.75 | 57.15 | 6.76 |
| FactorizePhys PURE (hazır)+Viterbi | 12.94 | 12.94 | 56.85 | 6.25 |
| MMRPhys 7E'den + UBFC-Phys (8. tur) | 14.31 | 14.31 | 53.67 | 12.14 |
| 7. tur B (MMRPhys sıfırdan) | 14.52 | 14.52 | 52.82 | 12.49 |
| 8. tur F en iyi epoch | 14.69 | 14.69 | 52.60 | 12.42 |
| 7. tur E son epoch (başlangıç) | 14.69 | 14.69 | 52.95 | 12.68 |
| FactorizePhys PURE (hazır) | 15.52 | 15.52 | 50.02 | 12.50 |
| 5. tur | 15.83 | 15.83 | 51.16 | 13.88 |
| 3. tur (uygulamadaki) | 15.88 | 15.88 | 50.71 | 13.99 |
| POS (yüz kırpıntısı)+Viterbi | 18.13 | 18.13 | 41.98 | 13.07 |
| POS (yüz kırpıntısı) | 20.06 | 20.06 | 37.44 | 17.73 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
