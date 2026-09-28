# Derin Öğrenme Karşılaştırması

rPPG-Toolbox'ın **PURE** veri setinde eğitilmiş hazır modelleri (ince ayar yok) aynı 28 videoda çalıştırıldı: UBFC-rPPG 8 denek + MCD-rPPG önden webcam 20 video (10 kişi, dinlenme / egzersiz sonrası). Modellerin ürettiği BVP sinyali bu projenin hattıyla nabza çevrildi: detrend + Butterworth, 10 s pencere, 1 s adım, argmax veya hareket güvenli Viterbi. Referans: parmak PPG'sinden pencere başına spektral tepe (diğer tablolarla aynı).

Ön işleme toolbox ile aynı: Haar yüz kutusu ×1.5, 30 karede bir yeniden tespit, 72×72 INTER_AREA, video başına DiffNormalized / Standardized. (FactorizePhys makalesinde YOLO5Face kullanılıyor; burada Haar kullanıldı.)

## Ortalama MAE (BPM)

| Yöntem | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % |
|---|---:|---:|---:|---:|---:|
| FactorizePhys + Viterbi | 2.02 | **2.31** | **3.12** | **2.51** | 89.4 |
| FactorizePhys (argmax) | **1.54** | 3.49 | 4.59 | 3.33 | 88.1 |
| POS tüm yüz + Viterbi (klasik) | 2.04 | 3.69 | 4.59 | 3.54 | 88.7 |
| POS 4 bölge ortalama + Viterbi | 1.96 | 4.09 | 7.60 | 4.73 | 85.5 |
| POS klasik (ortalama + argmax) | 1.68 | 5.77 | 7.87 | 5.35 | 84.2 |
| EfficientPhys + Viterbi | 2.04 | 12.41 | 16.72 | 10.99 | 53.8 |
| PhysNet + Viterbi | 8.45 | 13.06 | 21.47 | 14.75 | 48.3 |
| TS-CAN + Viterbi | 2.10 | 22.11 | 27.77 | 18.41 | 40.8 |

## Video bazında (FactorizePhys + Viterbi vs POS tüm yüz + Viterbi)

- 28 videonun **20'sinde fark ≤0.5 BPM**, 5'inde FactorizePhys daha iyi, 3'ünde daha kötü.
- Medyan MAE: POS **1.16**, FactorizePhys 1.36 BPM.
- Ortalamadaki kazancın neredeyse tamamı 3 zor videodan geliyor (1097 dinlenme/egzersiz, 1107 egzersiz): 23 → 10, 23 → 14, 15 → 9 BPM. Bu videolarda iki yöntem de başarısız, derin öğrenme hatayı yalnızca azaltıyor.

## Yorum

- Başka veri setinde eğitilmiş derin öğrenme modelleri **genel olarak klasik hattan iyi değil**. Dört modelden üçü MCD'de belirgin şekilde daha kötü (11–18 BPM); UBFC'de hepsi klasik hatla aynı düzeyde (1.5–2 BPM). Eğitim verisinden farklı kamera ve sıkıştırma koşullarına genelleme zayıf.
- En yeni model (FactorizePhys, 2024) tipik videolarda klasik hatla eşdeğer, en zor videolarda hatayı azaltıyor ama düzeltmiyor.
- Önerilen Viterbi takibi derin öğrenme çıktılarında da hatayı düşürüyor (FactorizePhys: 3.33 → 2.51).
- ~~Karar: klasik hat korunur.~~ Bu karar yalnızca **hazır** modeller için geçerliydi; ince ayardan sonra geçersiz (aşağıya bakın).

## Güncelleme: ince ayarlı FactorizePhys (2026-09-28)

FactorizePhys, test kişileri hariç MCD-rPPG (160 kişi, 3 kamera) + UBFC (3 denek) ile ince ayarlandı: 823 video, 27 saat. Ayrıntılar: [egitim/SONUCLAR.md](egitim/SONUCLAR.md).

| Yöntem (aynı 28 video) | UBFC | MCD dinlenme | MCD egzersiz | Hepsi | ≤5 BPM % |
|---|---:|---:|---:|---:|---:|
| **FactorizePhys ince ayarlı + Viterbi** | 1.76 | **0.88** | **1.06** | **1.19** | **95.3** |
| FactorizePhys PURE (hazır) + Viterbi | 1.42 | 2.19 | 3.88 | 2.57 | 88.9 |
| POS tüm yüz + Viterbi (klasik) | 2.04 | 3.69 | 4.59 | 3.54 | 88.7 |

- Ortalama hata klasik hatta göre 3.54 → 1.19 BPM. 28 videonun 13'ünde daha iyi, 14'ünde eşit (≤0.5 BPM), 1'inde daha kötü.
- Klasik hattın başarısız olduğu videolar düzeldi: 1097 dinlenme 23.2 → 3.0, 1097 egzersiz 23.0 → 5.2, 1107 egzersiz 14.5 → 0.6 BPM.
- UBFC'de hazır modelin biraz gerisinde (1.76 / 1.42). Eğitimde yalnızca 3 UBFC deneği var.
- Sınırlar: test kümesi küçük (28 video, 18 kişi), yalnızca önden webcam. Telefonda (tarayıcıda) çalıştırma henüz yapılmadı.
- Yeni karar: ince ayarlı model klasik hattan belirgin şekilde iyi. Sonraki adım, modeli mobil uygulamada çalıştırmak (ör. ONNX) ve telefon kamerasıyla doğrulamak.
