# MMRPhys 7E'den + UBFC-Phys (8. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) `results/derin_ogrenme/kaggle_tur7_E/last.pth` ağırlıklarından başlatılarak eğitildi. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_cohface`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 32 test videosu

| Yöntem | COHFACE | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 1.37 | 1.37 | 94.64 | 0.80 |
| 3. tur (uygulamadaki)+Viterbi | 1.37 | 1.37 | 94.64 | 0.87 |
| MMRPhys 7E'den + UBFC-Phys (8. tur)+Viterbi | 1.39 | 1.39 | 94.49 | 0.80 |
| 8. tur F en iyi epoch+Viterbi | 1.45 | 1.45 | 93.30 | 0.83 |
| 7. tur E son epoch (başlangıç)+Viterbi | 1.50 | 1.50 | 93.60 | 0.82 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.53 | 1.53 | 92.11 | 0.85 |
| 5. tur | 1.53 | 1.53 | 93.90 | 0.84 |
| 3. tur (uygulamadaki) | 1.69 | 1.69 | 93.01 | 0.93 |
| MMRPhys 7E'den + UBFC-Phys (8. tur) | 1.78 | 1.78 | 93.45 | 0.80 |
| 7. tur E son epoch (başlangıç) | 1.85 | 1.85 | 92.56 | 0.82 |
| 8. tur F en iyi epoch | 1.90 | 1.90 | 92.71 | 0.97 |
| 7. tur B (MMRPhys sıfırdan) | 2.00 | 2.00 | 91.52 | 0.85 |
| FactorizePhys PURE (hazır)+Viterbi | 9.29 | 9.29 | 49.55 | 7.65 |
| POS (yüz kırpıntısı)+Viterbi | 12.12 | 12.12 | 33.33 | 10.92 |
| FactorizePhys PURE (hazır) | 12.67 | 12.67 | 43.75 | 11.60 |
| POS (yüz kırpıntısı) | 13.78 | 13.78 | 36.90 | 14.16 |

## Referans etiketi temiz test videoları (32/32)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: .

| Yöntem | COHFACE | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 1.37 | 1.37 | 94.64 | 0.80 |
| 3. tur (uygulamadaki)+Viterbi | 1.37 | 1.37 | 94.64 | 0.87 |
| MMRPhys 7E'den + UBFC-Phys (8. tur)+Viterbi | 1.39 | 1.39 | 94.49 | 0.80 |
| 8. tur F en iyi epoch+Viterbi | 1.45 | 1.45 | 93.30 | 0.83 |
| 7. tur E son epoch (başlangıç)+Viterbi | 1.50 | 1.50 | 93.60 | 0.82 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.53 | 1.53 | 92.11 | 0.85 |
| 5. tur | 1.53 | 1.53 | 93.90 | 0.84 |
| 3. tur (uygulamadaki) | 1.69 | 1.69 | 93.01 | 0.93 |
| MMRPhys 7E'den + UBFC-Phys (8. tur) | 1.78 | 1.78 | 93.45 | 0.80 |
| 7. tur E son epoch (başlangıç) | 1.85 | 1.85 | 92.56 | 0.82 |
| 8. tur F en iyi epoch | 1.90 | 1.90 | 92.71 | 0.97 |
| 7. tur B (MMRPhys sıfırdan) | 2.00 | 2.00 | 91.52 | 0.85 |
| FactorizePhys PURE (hazır)+Viterbi | 9.29 | 9.29 | 49.55 | 7.65 |
| POS (yüz kırpıntısı)+Viterbi | 12.12 | 12.12 | 33.33 | 10.92 |
| FactorizePhys PURE (hazır) | 12.67 | 12.67 | 43.75 | 11.60 |
| POS (yüz kırpıntısı) | 13.78 | 13.78 | 36.90 | 14.16 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
