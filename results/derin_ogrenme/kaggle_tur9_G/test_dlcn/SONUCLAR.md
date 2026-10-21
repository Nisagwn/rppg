# MMRPhys 7E'den + yeni teknikler (9. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) `results/derin_ogrenme/kaggle_tur7_E/last.pth` ağırlıklarından başlatılarak eğitildi. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_dlcn`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 152 test videosu

| Yöntem | DLCN gece dinlenme | DLCN gece egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|
| 7. tur E son epoch (başlangıç)+Viterbi | 1.08 | 1.54 | 1.31 | 95.39 | 0.75 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 0.96 | 1.95 | 1.45 | 94.99 | 0.73 |
| 9. tur G en iyi epoch+Viterbi | 1.21 | 1.79 | 1.50 | 94.74 | 0.74 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.05 | 2.33 | 1.69 | 94.24 | 0.82 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 1.64 | 3.36 | 2.50 | 92.61 | 0.80 |
| 7. tur E son epoch (başlangıç) | 1.66 | 3.34 | 2.50 | 92.29 | 0.80 |
| 9. tur G en iyi epoch | 2.00 | 3.30 | 2.65 | 91.73 | 0.83 |
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
| 7. tur E son epoch (başlangıç)+Viterbi | 1.08 | 1.54 | 1.31 | 95.39 | 0.75 |
| MMRPhys 7E'den + yeni teknikler (9. tur)+Viterbi | 0.96 | 1.95 | 1.45 | 94.99 | 0.73 |
| 9. tur G en iyi epoch+Viterbi | 1.21 | 1.79 | 1.50 | 94.74 | 0.74 |
| 7. tur B (MMRPhys sıfırdan)+Viterbi | 1.05 | 2.33 | 1.69 | 94.24 | 0.82 |
| MMRPhys 7E'den + yeni teknikler (9. tur) | 1.64 | 3.36 | 2.50 | 92.61 | 0.80 |
| 7. tur E son epoch (başlangıç) | 1.66 | 3.34 | 2.50 | 92.29 | 0.80 |
| 9. tur G en iyi epoch | 2.00 | 3.30 | 2.65 | 91.73 | 0.83 |
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
