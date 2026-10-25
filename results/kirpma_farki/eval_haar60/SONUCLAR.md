# 5. tur — Test Sonuçları

FactorizePhys (rPPG-Toolbox) eğitildi (başlangıç ağırlıkları eğitim günlüğünde). Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_haar60`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

## Eğitim verisi

- 0 video, 0 kişi, 0.0 saat (yüz bulunma oranı <%50 olan 0 video çıkarıldı)
- MCD: 0 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), video başına ilk 0 s
- UBFC: 0 denek
- PURE: 0 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: negatif Pearson; AdamW, cosine öğrenme oranı
- Seçim: en iyi epoch doğrulama kişilerinde pencere MAE (argmax) ile

Eğitim: 100 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 2.72 → en iyi 2.27 BPM (epoch 45).

## Ortalama MAE (BPM) — 48 test videosu

| Yöntem | MCD dinlenme | MCD egzersiz | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 0.80 | 0.92 | 2.30 | 2.16 | 1.09 | 1.07 | 1.31 | 94.68 | 0.65 |
| 5. tur | 1.43 | 1.27 | 3.71 | 3.89 | 1.69 | 1.64 | 2.16 | 92.42 | 0.71 |
| FactorizePhys PURE (hazır)+Viterbi | 2.19 | 3.88 | 5.75 | 8.43 | 9.07 | 6.83 | 5.62 | 71.00 | 3.49 |
| FactorizePhys PURE (hazır) | 3.42 | 4.78 | 9.80 | 13.27 | 14.16 | 11.43 | 8.78 | 64.37 | 8.45 |
| POS (yüz kırpıntısı)+Viterbi | 5.73 | 6.12 | 12.29 | 14.25 | 15.67 | 18.53 | 11.59 | 53.05 | 6.35 |
| POS (yüz kırpıntısı) | 6.50 | 7.64 | 16.01 | 16.31 | 20.23 | 18.43 | 13.20 | 50.94 | 11.75 |

## Referans etiketi temiz test videoları (48/48)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: .

| Yöntem | MCD dinlenme | MCD egzersiz | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 0.80 | 0.92 | 2.30 | 2.16 | 1.09 | 1.07 | 1.31 | 94.68 | 0.65 |
| 5. tur | 1.43 | 1.27 | 3.71 | 3.89 | 1.69 | 1.64 | 2.16 | 92.42 | 0.71 |
| FactorizePhys PURE (hazır)+Viterbi | 2.19 | 3.88 | 5.75 | 8.43 | 9.07 | 6.83 | 5.62 | 71.00 | 3.49 |
| FactorizePhys PURE (hazır) | 3.42 | 4.78 | 9.80 | 13.27 | 14.16 | 11.43 | 8.78 | 64.37 | 8.45 |
| POS (yüz kırpıntısı)+Viterbi | 5.73 | 6.12 | 12.29 | 14.25 | 15.67 | 18.53 | 11.59 | 53.05 | 6.35 |
| POS (yüz kırpıntısı) | 6.50 | 7.64 | 16.01 | 16.31 | 20.23 | 18.43 | 13.20 | 50.94 | 11.75 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
