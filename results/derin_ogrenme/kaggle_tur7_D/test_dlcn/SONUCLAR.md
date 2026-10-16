# MMRPhys B'den ince ayar (7. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **7. tur B'nin en iyi modelinden** (kendi sıfırdan eğittiğimiz ağırlıklar, `kaggle_tur7_B/best.pth`) başlatılarak DLCN ve COHFACE eklenmiş veriyle ince ayarlandı (lr 2e-4, 100 epoch); dışarıdan hazır ağırlık kullanılmadı. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_dlcn`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 152 test videosu

| Yöntem | DLCN gece dinlenme | DLCN gece egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 0.88 | 1.73 | 1.31 | 96.37 | 0.69 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 0.89 | 1.85 | 1.37 | 96.40 | 0.69 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.05 | 2.33 | 1.69 | 94.24 | 0.82 |
| MMRPhys B'den ince ayar (7. tur) | 1.42 | 2.84 | 2.13 | 94.11 | 0.75 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 1.65 | 2.89 | 2.27 | 93.42 | 0.75 |
| 5. tur+Viterbi | 1.93 | 3.73 | 2.83 | 87.72 | 1.10 |
| 7. tur B (MMRPhys sıfırdan) | 2.06 | 3.70 | 2.88 | 90.95 | 0.92 |
| 3. tur (uygulamadaki)+Viterbi | 1.87 | 4.38 | 3.13 | 87.28 | 1.08 |
| FactorizePhys PURE (hazır)+Viterbi | 2.58 | 6.59 | 4.58 | 82.86 | 1.31 |
| 5. tur | 3.80 | 6.06 | 4.93 | 82.46 | 2.15 |
| 3. tur (uygulamadaki) | 3.98 | 6.18 | 5.08 | 82.36 | 2.24 |
| FactorizePhys PURE (hazır) | 4.88 | 8.08 | 6.48 | 77.04 | 3.10 |
| POS (yüz kırpıntısı)+Viterbi | 5.99 | 14.71 | 10.35 | 68.42 | 2.56 |
| POS (yüz kırpıntısı) | 9.04 | 15.26 | 12.15 | 64.25 | 7.82 |

## Referans etiketi temiz test videoları (152/152)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: .

| Yöntem | DLCN gece dinlenme | DLCN gece egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| MMRPhys B'den ince ayar (7. tur)+Viterbi | 0.88 | 1.73 | 1.31 | 96.37 | 0.69 |
| MMRPhys B'den ince ayar (7. tur) (son epoch)+Viterbi | 0.89 | 1.85 | 1.37 | 96.40 | 0.69 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.05 | 2.33 | 1.69 | 94.24 | 0.82 |
| MMRPhys B'den ince ayar (7. tur) | 1.42 | 2.84 | 2.13 | 94.11 | 0.75 |
| MMRPhys B'den ince ayar (7. tur) (son epoch) | 1.65 | 2.89 | 2.27 | 93.42 | 0.75 |
| 5. tur+Viterbi | 1.93 | 3.73 | 2.83 | 87.72 | 1.10 |
| 7. tur B (MMRPhys sıfırdan) | 2.06 | 3.70 | 2.88 | 90.95 | 0.92 |
| 3. tur (uygulamadaki)+Viterbi | 1.87 | 4.38 | 3.13 | 87.28 | 1.08 |
| FactorizePhys PURE (hazır)+Viterbi | 2.58 | 6.59 | 4.58 | 82.86 | 1.31 |
| 5. tur | 3.80 | 6.06 | 4.93 | 82.46 | 2.15 |
| 3. tur (uygulamadaki) | 3.98 | 6.18 | 5.08 | 82.36 | 2.24 |
| FactorizePhys PURE (hazır) | 4.88 | 8.08 | 6.48 | 77.04 | 3.10 |
| POS (yüz kırpıntısı)+Viterbi | 5.99 | 14.71 | 10.35 | 68.42 | 2.56 |
| POS (yüz kırpıntısı) | 9.04 | 15.26 | 12.15 | 64.25 | 7.82 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
