# İnce Ayarlı FactorizePhys (Kaggle, büyük veri) — Test Sonuçları

Yerelde epoch 73'te kalan eğitim Kaggle'da (Tesla T4) 200 epoch'a tamamlandı ve önceki karşılaştırmanın aynı 28 videosunda
(UBFC 8 denek + MCD önden webcam 20 video, 10 kişi) değerlendirildi. Test kişileri eğitim ve doğrulamada hiç kullanılmadı.
Değerlendirme yerelde yapıldı (Kaggle'da test kümesi hazırlanamadı, aşağıya bakın); test videoları yerel kümeyle bire bir aynı.

## Eğitim verisi (Kaggle)

- MCD-rPPG: 590 kişi × 3 kamera × {dinlenme, egzersiz} = 3540 video işlendi, ilk 45 s; yüz bulunma oranı <%50 olan 534 video
  (çoğu yan kamera) ve referansı bozuk olanlar çıkarıldı
- PURE: 60 oturumun 59'u (10 kişi × 6 hareket senaryosu; HF kopyası)
- **UBFC-rPPG: yok.** Kaggle'da UBFC videolarını (sıkıştırılmamış, 1.8 GB) işleyen süreç çöktü (`BrokenProcessPool`);
  model UBFC'siz eğitildi. Yerel ilk 73 epoch'ta 34 UBFC deneği vardı.
- Son epoch'ta eğitim kümesi: 2721 video, 534 kişi; kişilerin ~%10'u doğrulamada
- Ön işleme toolbox ile aynı (Haar ×1.5, 30 karede bir tespit, 72×72, ham kare); hepsi 30 fps'e yeniden örneklendi
- MCD parmak PPG'si UBFC/PURE'a göre ters işaretli; eğitimde ters çevrildi. Düz (sensörsüz) referanslı videolar elendi.
- Artırma (GPU'da): yatay çevirme, hız 0.8–1.25×, parlaklık ×0.8–1.2. Kayıp: negatif Pearson; AdamW, cosine öğrenme oranı.

Eğitim: 200 epoch (500 adım × 8 parça), Kaggle'da 7 saat. En iyi doğrulama MAE 2.26 BPM (epoch 84); sonrasında 2.6–2.9
arasında kaldı (doygunluk). Tablodaki "ince ayarlı" = epoch 84, "son epoch" = epoch 200.

## Önceki modelle karşılaştırma (160 kişi, 43 epoch; aynı 28 video, Viterbi)

| Model | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | Medyan |
|---|---:|---:|---:|---:|---:|
| Önceki (MCD 160 kişi + UBFC 3) | 1.76 | 0.88 | 1.06 | 1.19 | 0.57 |
| Kaggle en iyi (epoch 84) | 1.81 | 0.85 | 1.02 | 1.19 | 0.57 |
| Kaggle son (epoch 200) | 1.71 | 0.84 | 1.07 | 1.17 | 0.55 |

- **Fark yok:** 28 videonun 26'sında iki model arasındaki fark ≤0.5 BPM. Veri ~3.5 kat büyüdü ama bu test kümesinde kazanç olmadı.
- Test kümesi doymuş görünüyor: medyan hata 0.57 BPM (referansın kendi ölçüm belirsizliği düzeyinde); ortalamayı birkaç zor video
  belirliyor (1097 dinlenme/egzersiz, UBFC subject3/subject4) ve bunlar iki modelde de aynı kaldı.
- Daha geniş verinin olası faydası (farklı kişiler, kameralar, hareket) bu test kümesiyle ölçülemiyor: test yalnızca önden webcam.
  Telefonla toplanacak veri bu soruyu cevaplar.

## Ortalama MAE (BPM) — 28 test videosu

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|
| FactorizePhys ince ayarlı (son epoch)+Viterbi | 1.71 | 0.84 | 1.07 | 1.17 | 95.38 | 0.55 |
| FactorizePhys ince ayarlı+Viterbi | 1.81 | 0.85 | 1.02 | 1.19 | 94.91 | 0.57 |
| FactorizePhys ince ayarlı (son epoch) | 1.06 | 1.34 | 1.31 | 1.25 | 96.54 | 0.52 |
| FactorizePhys ince ayarlı | 1.12 | 1.53 | 1.38 | 1.36 | 95.64 | 0.53 |
| FactorizePhys PURE (hazır)+Viterbi | 1.42 | 2.19 | 3.88 | 2.57 | 88.94 | 1.07 |
| FactorizePhys PURE (hazır) | 1.00 | 3.42 | 4.78 | 3.21 | 88.56 | 1.33 |
| POS tüm yüz+Viterbi | 2.04 | 3.69 | 4.59 | 3.54 | 88.70 | 1.16 |
| POS ortalama+Viterbi | 1.96 | 4.09 | 7.60 | 4.73 | 85.54 | 1.38 |
| POS klasik (ortalama+argmax) | 1.68 | 5.77 | 7.87 | 5.35 | 84.18 | 2.43 |

## Video bazında (ince ayarlı + Viterbi vs POS tüm yüz + Viterbi)

- 28 videonun 13'inde fark ≤0.5 BPM, 14'inde ince ayarlı model daha iyi, 1'inde daha kötü.

En zor 5 video (POS'a göre):

| Video | POS+Viterbi | PURE hazır+Viterbi | İnce ayarlı+Viterbi |
|---|---:|---:|---:|
| 1097_FullHDwebcam_before | 23.17 | 9.10 | 3.45 |
| 1097_FullHDwebcam_after | 23.03 | 11.00 | 4.71 |
| 1107_FullHDwebcam_after | 14.53 | 19.98 | 0.56 |
| 1107_FullHDwebcam_before | 5.71 | 4.33 | 0.58 |
| subject4 | 4.87 | 3.86 | 4.93 |

Ayrıntı: `test_sonuclari.csv` (video × yöntem), `test_ozet.csv`, `gecmis.json` (epoch geçmişi).
Yeniden üretmek: `scripts/dl_prepare.py` → `scripts/dl_train.py` → `scripts/dl_evaluate.py` (ya da hepsi: `scripts/dl_pipeline.py`).
