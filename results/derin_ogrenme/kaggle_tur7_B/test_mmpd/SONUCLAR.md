# MMRPhys sıfırdan (7. tur) — Test Sonuçları

MMRPhys (Joshi ve Cho 2025) **rastgele başlatılarak (sıfırdan)** eğitildi; hiçbir hazır ağırlık kullanılmadı. Eğitimde yalnızca test **dışı** kişiler kullanıldı; test kişileri eğitim ve doğrulamada hiç kullanılmadı. Kaggle'da üç oturumda (epoch 1-37, 38-78, 79-150; `last.pth`'den devam).

## Eğitim verisi

- MCD + UBFC + PURE: 2889 video, 595 kişi, 36.8 saat (yüz bulunma oranı <%50 olan 509 video çıkarıldı)
- MCD: 2797 video (3 kamera: önden webcam, sol USB, sağ telefon; dinlenme + egzersiz sonrası), ilk 45 s
- UBFC: 34 denek
- PURE: 58 oturum (10 kişi × 6 hareket senaryosu; HF kopyası)
- VIPL-HR (source1/3): 1104 videonun 866'sı (etiket 5. tur modeliyle video başına hizalandı; hizalı korelasyonu < 0.4 olanlar çıkarıldı; source2 hiç kullanılmadı)
- DLCN ve COHFACE bu oturumda girmedi (DLCN girdisi eklenmemişti; COHFACE dosya listesi anahtarsız istendiği için alınamadı)
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli model çıktısıyla korelasyon ≈ −0.75, gecikme ≈ 0); eğitimde ters çevrildi
- Artırma: yatay çevirme, hız 0.8–1.25× (HR aralığını genişletir), parlaklık ×0.8–1.2
- Kayıp: SmoothL1 (standartlaştırılmış tahmin ve etiket; TSFM eğitimde etiketi kısıt olarak kullanır); AdamW, cosine öğrenme oranı; en iyi epoch doğrulama kişilerinde pencere MAE ile seçildi

Eğitim: 150 epoch (500 adım × 8 parça). Doğrulama MAE: rastgele başlangıç 45.00 → en iyi 1.86 BPM (epoch 137).

## Ortalama MAE (BPM) — 115 test videosu

| Yöntem | MMPD (telefon) | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|
| 5. tur+Viterbi | 12.65 | 12.65 | 56.77 | 6.74 |
| 3. tur (uygulamadaki)+Viterbi | 13.23 | 13.23 | 56.66 | 6.88 |
| MMRPhys sıfırdan (7. tur)+Viterbi | 13.24 | 13.24 | 56.10 | 6.64 |
| MMRPhys sıfırdan (7. tur) (son epoch)+Viterbi | 13.30 | 13.30 | 56.12 | 6.63 |
| FactorizePhys PURE (hazır)+Viterbi | 13.71 | 13.71 | 55.18 | 6.56 |
| MMRPhys sıfırdan (7. tur) | 15.48 | 15.48 | 50.89 | 12.86 |
| MMRPhys sıfırdan (7. tur) (son epoch) | 15.66 | 15.66 | 50.78 | 13.11 |
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
| MMRPhys sıfırdan (7. tur) (son epoch)+Viterbi | 12.26 | 12.26 | 58.09 | 5.99 |
| MMRPhys sıfırdan (7. tur)+Viterbi | 12.27 | 12.27 | 58.13 | 6.16 |
| FactorizePhys PURE (hazır)+Viterbi | 12.94 | 12.94 | 56.85 | 6.25 |
| MMRPhys sıfırdan (7. tur) | 14.52 | 14.52 | 52.82 | 12.49 |
| MMRPhys sıfırdan (7. tur) (son epoch) | 14.68 | 14.68 | 52.75 | 12.85 |
| FactorizePhys PURE (hazır) | 15.52 | 15.52 | 50.02 | 12.50 |
| 5. tur | 15.83 | 15.83 | 51.16 | 13.88 |
| 3. tur (uygulamadaki) | 15.88 | 15.88 | 50.71 | 13.99 |
| POS (yüz kırpıntısı)+Viterbi | 18.13 | 18.13 | 41.98 | 13.07 |
| POS (yüz kırpıntısı) | 20.06 | 20.06 | 37.44 | 17.73 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
