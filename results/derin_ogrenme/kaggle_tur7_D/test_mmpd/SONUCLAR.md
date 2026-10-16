# MMRPhys B'den ince ayar (7. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **7. tur B'nin en iyi modelinden** (kendi sıfırdan eğittiğimiz ağırlıklar, `kaggle_tur7_B/best.pth`) başlatılarak DLCN ve COHFACE eklenmiş veriyle ince ayarlandı (lr 2e-4, 100 epoch); dışarıdan hazır ağırlık kullanılmadı. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_mmpd`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

## Eğitim verisi

- 4959 video, 831 kişi, 42.8 saat (yüz bulunma oranı <%50 olan 564 video çıkarıldı)
- MCD: 3003 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), video başına ilk 30 s
- UBFC: 34 denek
- PURE: 58 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- VIPL-HR (source1/3): 1104 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- DLCN: 628 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- COHFACE: 132 video (etiket model tabanlı video başına hizalandı; hizalı korelasyonu zayıf olanlar eğitimde çıkarıldı)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır); AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi

Eğitim: 100 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 2.05 → en iyi 1.48 BPM (epoch 47).

## Ortalama MAE (BPM) — 115 test videosu

| Yöntem | MMPD (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 12.65 | 12.65 | 56.77 | 6.74 |
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 13.17 | 13.17 | 56.23 | 6.86 |
| 3. tur (uygulamadaki)+Viterbi | 13.23 | 13.23 | 56.66 | 6.88 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 13.24 | 13.24 | 56.10 | 6.64 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 13.58 | 13.58 | 54.85 | 7.39 |
| FactorizePhys PURE (hazır)+Viterbi | 13.71 | 13.71 | 55.18 | 6.56 |
| MMRPhys B'den ince ayar (7. tur) | 15.10 | 15.10 | 52.64 | 12.22 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 15.34 | 15.34 | 51.79 | 12.33 |
| 7. tur B (MMRPhys sıfırdan) | 15.48 | 15.48 | 50.89 | 12.86 |
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
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 12.08 | 12.08 | 58.20 | 6.29 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 12.27 | 12.27 | 58.13 | 6.16 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 12.61 | 12.61 | 56.78 | 6.42 |
| FactorizePhys PURE (hazır)+Viterbi | 12.94 | 12.94 | 56.85 | 6.25 |
| MMRPhys B'den ince ayar (7. tur) | 14.12 | 14.12 | 54.65 | 11.75 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 14.37 | 14.37 | 53.75 | 12.05 |
| 7. tur B (MMRPhys sıfırdan) | 14.52 | 14.52 | 52.82 | 12.49 |
| FactorizePhys PURE (hazır) | 15.52 | 15.52 | 50.02 | 12.50 |
| 5. tur | 15.83 | 15.83 | 51.16 | 13.88 |
| 3. tur (uygulamadaki) | 15.88 | 15.88 | 50.71 | 13.99 |
| POS (yüz kırpıntısı)+Viterbi | 18.13 | 18.13 | 41.98 | 13.07 |
| POS (yüz kırpıntısı) | 20.06 | 20.06 | 37.44 | 17.73 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
