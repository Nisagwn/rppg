# MMRPhys sıfırdan, yalnızca PURE (standart protokol) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **rastgele başlatılarak (sıfırdan)** eğitildi; hiçbir hazır ağırlık kullanılmadı. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kümesi `test_ubfc_hepsi`. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.

> **Not (20 Eki):** Eğitim 1. oturumda yapıldı (PURE'un 59 oturumu; yalnızca PURE'dan örneklendi, `--source-weights pure=1`;
> günlük `../gunlukler/egitim_oturum1.log`). Değerlendirme 1. oturumda dosya adı hatasıyla çöktü, 2. oturumda
> GPU'suz yalnızca değerlendirme yapıldı; aşağıdaki veri sayıları 2. oturumda diskte olanlar (PURE hazırlığı yarıda
> kesildi). UBFC'nin 34 eğitim kişisi **eğitimde kullanılmadı**, yalnızca bu test kümesine (42 kişi) girdi.
> "FactorizePhys PURE (hazır)": rPPG-Toolbox'un PURE'da eğitilmiş resmî ağırlıkları, yani aynı protokol; aynı
> ön işleme ve aynı metrikle (10 s pencere MAE) ölçüldü.

## Eğitim verisi

- 50 video, 37 kişi, 0.9 saat (yüz bulunma oranı <%50 olan 0 video çıkarıldı)
- MCD: 0 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), video başına ilk 0 s
- UBFC: 34 denek
- PURE: 16 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır); AdamW, cosine öğrenme oranı
- Seçim: en iyi epoch doğrulama kişilerinde pencere MAE (argmax) ile

Eğitim: 30 epoch (500 adım × 8 parça). Doğrulama MAE: başlangıç 37.24 → en iyi 0.53 BPM (epoch 6).

## Ortalama MAE (BPM) — 42 test videosu

| Yöntem | UBFC | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| FactorizePhys PURE (hazır) | 0.68 | 0.68 | 98.71 | 0.45 |
| MMRPhys sıfırdan, yalnızca PURE (standart protokol) | 0.74 | 0.74 | 98.46 | 0.54 |
| 9. tur S1 en iyi epoch | 0.77 | 0.77 | 98.56 | 0.48 |
| FactorizePhys PURE (hazır)+Viterbi | 0.82 | 0.82 | 97.72 | 0.48 |
| MMRPhys sıfırdan, yalnızca PURE (standart protokol)+Viterbi | 0.83 | 0.83 | 97.76 | 0.57 |
| 9. tur S1 en iyi epoch+Viterbi | 0.88 | 0.88 | 97.40 | 0.51 |
| POS (yüz kırpıntısı)+Viterbi | 1.86 | 1.86 | 94.66 | 0.72 |
| POS (yüz kırpıntısı) | 2.63 | 2.63 | 92.71 | 0.88 |

## Referans etiketi temiz test videoları (40/42)

Referans sensör sinyalinin ≥%80'i iyi olan videolar (`scripts/dl_quality.py`: SNR ≥ 0 dB, nabız 40–180, sıçrama yok). Çıkarılanlar: subject3 (iyi %57, SNR 1.8 dB), subject4 (iyi %39, SNR -0.4 dB).

| Yöntem | UBFC | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| FactorizePhys PURE (hazır) | 0.62 | 0.62 | 98.95 | 0.44 |
| MMRPhys sıfırdan, yalnızca PURE (standart protokol)+Viterbi | 0.68 | 0.68 | 98.63 | 0.54 |
| MMRPhys sıfırdan, yalnızca PURE (standart protokol) | 0.68 | 0.68 | 98.75 | 0.50 |
| 9. tur S1 en iyi epoch | 0.68 | 0.68 | 98.93 | 0.47 |
| FactorizePhys PURE (hazır)+Viterbi | 0.69 | 0.69 | 98.41 | 0.47 |
| 9. tur S1 en iyi epoch+Viterbi | 0.70 | 0.70 | 98.50 | 0.49 |
| POS (yüz kırpıntısı)+Viterbi | 1.73 | 1.73 | 95.65 | 0.70 |
| POS (yüz kırpıntısı) | 2.64 | 2.64 | 92.83 | 0.84 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
