# MMRPhys B'den ince ayar (7. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **7. tur B'nin en iyi modelinden** (kendi sıfırdan eğittiğimiz ağırlıklar, `kaggle_tur7_B/best.pth`) başlatılarak DLCN ve COHFACE eklenmiş veriyle ince ayarlandı (lr 2e-4, 100 epoch); dışarıdan hazır ağırlık kullanılmadı. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_kamera`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 28 test videosu

| Yöntem | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 2.30 | 2.16 | 1.09 | 1.07 | 1.64 | 92.84 | 0.97 |
| 3. tur (uygulamadaki)+Viterbi | 2.62 | 2.23 | 1.07 | 1.03 | 1.71 | 92.59 | 0.94 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 2.44 | 2.76 | 1.34 | 1.26 | 1.96 | 91.47 | 1.25 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 3.50 | 3.05 | 1.50 | 1.26 | 2.27 | 89.91 | 1.22 |
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 2.87 | 3.62 | 1.52 | 1.31 | 2.36 | 89.34 | 1.33 |
| 5. tur | 3.71 | 3.89 | 1.69 | 1.64 | 2.74 | 89.59 | 1.05 |
| 3. tur (uygulamadaki) | 3.75 | 3.84 | 1.78 | 1.84 | 2.82 | 89.07 | 1.11 |
| 7. tur B (MMRPhys sıfırdan) | 4.96 | 4.82 | 2.71 | 2.72 | 3.80 | 86.33 | 2.01 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 4.95 | 5.08 | 2.70 | 2.56 | 3.82 | 86.01 | 1.71 |
| MMRPhys B'den ince ayar (7. tur) | 4.84 | 5.35 | 2.71 | 2.67 | 3.92 | 85.36 | 1.78 |
| FactorizePhys PURE (hazır)+Viterbi | 6.37 | 8.43 | 9.07 | 6.83 | 7.58 | 59.21 | 5.43 |
| FactorizePhys PURE (hazır) | 9.80 | 13.27 | 14.16 | 11.43 | 12.12 | 49.59 | 11.12 |
| POS (yüz kırpıntısı)+Viterbi | 12.29 | 14.25 | 15.67 | 18.53 | 15.63 | 33.05 | 13.66 |
| POS (yüz kırpıntısı) | 16.01 | 16.31 | 20.23 | 18.43 | 17.58 | 31.97 | 16.41 |

## Referans etiketi temiz test videoları (28/28)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: .

| Yöntem | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 2.30 | 2.16 | 1.09 | 1.07 | 1.64 | 92.84 | 0.97 |
| 3. tur (uygulamadaki)+Viterbi | 2.62 | 2.23 | 1.07 | 1.03 | 1.71 | 92.59 | 0.94 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 2.44 | 2.76 | 1.34 | 1.26 | 1.96 | 91.47 | 1.25 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 3.50 | 3.05 | 1.50 | 1.26 | 2.27 | 89.91 | 1.22 |
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 2.87 | 3.62 | 1.52 | 1.31 | 2.36 | 89.34 | 1.33 |
| 5. tur | 3.71 | 3.89 | 1.69 | 1.64 | 2.74 | 89.59 | 1.05 |
| 3. tur (uygulamadaki) | 3.75 | 3.84 | 1.78 | 1.84 | 2.82 | 89.07 | 1.11 |
| 7. tur B (MMRPhys sıfırdan) | 4.96 | 4.82 | 2.71 | 2.72 | 3.80 | 86.33 | 2.01 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 4.95 | 5.08 | 2.70 | 2.56 | 3.82 | 86.01 | 1.71 |
| MMRPhys B'den ince ayar (7. tur) | 4.84 | 5.35 | 2.71 | 2.67 | 3.92 | 85.36 | 1.78 |
| FactorizePhys PURE (hazır)+Viterbi | 6.37 | 8.43 | 9.07 | 6.83 | 7.58 | 59.21 | 5.43 |
| FactorizePhys PURE (hazır) | 9.80 | 13.27 | 14.16 | 11.43 | 12.12 | 49.59 | 11.12 |
| POS (yüz kırpıntısı)+Viterbi | 12.29 | 14.25 | 15.67 | 18.53 | 15.63 | 33.05 | 13.66 |
| POS (yüz kırpıntısı) | 16.01 | 16.31 | 20.23 | 18.43 | 17.58 | 31.97 | 16.41 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
