# 5. tur — Test Sonuçları

FactorizePhys (rPPG-Toolbox) eğitildi (başlangıç ağırlıkları eğitim günlüğünde). Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_app`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

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

## Ortalama MAE (BPM) — 60 test videosu

| Yöntem | MCD dinlenme | MCD egzersiz | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 0.79 | 1.20 | 2.15 | 2.61 | 1.41 | 1.63 | 1.63 | 93.47 | 0.77 |
| 5. tur | 1.14 | 1.22 | 3.93 | 3.58 | 2.99 | 2.36 | 2.54 | 90.85 | 0.77 |
| FactorizePhys PURE (hazır)+Viterbi | 1.93 | 1.89 | 7.55 | 6.68 | 11.20 | 4.72 | 5.66 | 73.05 | 2.91 |
| FactorizePhys PURE (hazır) | 3.04 | 3.51 | 12.39 | 10.36 | 14.75 | 10.26 | 9.05 | 65.40 | 7.72 |
| POS (yüz kırpıntısı)+Viterbi | 3.85 | 3.63 | 10.38 | 12.76 | 18.72 | 15.27 | 10.77 | 58.71 | 5.73 |
| POS (yüz kırpıntısı) | 5.33 | 6.09 | 14.89 | 15.29 | 23.89 | 18.35 | 13.97 | 53.54 | 12.78 |

## Referans etiketi temiz test videoları (60/60)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: .

| Yöntem | MCD dinlenme | MCD egzersiz | MCD dinlenme (USB) | MCD dinlenme (telefon) | MCD egzersiz (USB) | MCD egzersiz (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5. tur+Viterbi | 0.79 | 1.20 | 2.15 | 2.61 | 1.41 | 1.63 | 1.63 | 93.47 | 0.77 |
| 5. tur | 1.14 | 1.22 | 3.93 | 3.58 | 2.99 | 2.36 | 2.54 | 90.85 | 0.77 |
| FactorizePhys PURE (hazır)+Viterbi | 1.93 | 1.89 | 7.55 | 6.68 | 11.20 | 4.72 | 5.66 | 73.05 | 2.91 |
| FactorizePhys PURE (hazır) | 3.04 | 3.51 | 12.39 | 10.36 | 14.75 | 10.26 | 9.05 | 65.40 | 7.72 |
| POS (yüz kırpıntısı)+Viterbi | 3.85 | 3.63 | 10.38 | 12.76 | 18.72 | 15.27 | 10.77 | 58.71 | 5.73 |
| POS (yüz kırpıntısı) | 5.33 | 6.09 | 14.89 | 15.29 | 23.89 | 18.35 | 13.97 | 53.54 | 12.78 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
