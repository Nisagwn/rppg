# Telefon ve USB Kamera Testi

Bu testte ana testteki 10 MCD test kişisinin **telefon (IriunWebcam)** ve **USB kamera** videoları kullanıldı. Bu
kişiler hiçbir turda eğitimde ya da doğrulamada kullanılmadı. Ana test yalnızca önden webcam videolarından oluşuyor.
Burada aynı kişiler telefon kamerasıyla ve yandan bir açıyla ölçülüyor.

- Toplam 40 video indirildi. Yüzün karelerin yarısından azında bulunduğu 12 video dışarıda kaldı (eğitimdeki kural).
  Bunların 11'i USB kamera videosu: USB kamera yandan çekiyor ve yüz algılayıcı yüzü bulamıyor.
- Teste giren 28 video:
  - telefon: dinlenme 9, egzersiz sonrası 10
  - USB: dinlenme 5, egzersiz sonrası 4
- Ön işleme ana testle aynı: tam çözünürlükte Haar, 72×72 kırpıntı, video süresinin tamamı (~3 dk).
- Hata ölçümü de ana testle aynı: 10 s pencere, 1 s adım, parmak PPG'sinden referans nabız.
- Taban çizgisi "POS (yüz kırpıntısı)": modelle aynı kırpıntının ortasından hesaplanan klasik POS sinyali.
- Modeller işlemcide çalıştırıldı: `scripts/dl_evaluate.py --test data/dl/test_kamera`.

## Ortalama MAE (BPM)

| Yöntem | Dinlenme USB | Dinlenme telefon | Egzersiz USB | Egzersiz telefon | Hepsi | ≤5 BPM % | Medyan |
|---|---:|---:|---:|---:|---:|---:|---:|
| **3. tur (temiz etiket, son epoch)** + Viterbi | 2.62 | 2.23 | 1.07 | 1.03 | **1.71** | 92.6 | 0.94 |
| 2. tur (son epoch) + Viterbi | 2.26 | 2.82 | 1.62 | 1.00 | 1.90 | 91.3 | 0.94 |
| 1. tur (uygulamadaki) + Viterbi | 2.44 | 2.92 | 1.32 | 1.09 | 1.95 | 90.6 | 0.87 |
| **3. tur**, argmax | 3.75 | 3.84 | 1.78 | 1.84 | **2.82** | 89.1 | 1.11 |
| 2. tur, argmax | 4.40 | 4.15 | 2.68 | 1.89 | 3.18 | 88.2 | 1.25 |
| 1. tur, argmax | 5.59 | 4.61 | 3.16 | 2.16 | 3.70 | 86.6 | 1.83 |
| PURE ön-eğitimli (hazır) + Viterbi | 5.75 | 8.43 | 9.07 | 6.83 | 7.47 | 59.8 | 5.43 |
| POS (yüz kırpıntısı) + Viterbi | 12.29 | 14.25 | 15.67 | 18.53 | 15.63 | 33.1 | 13.66 |

## Yorum

- **Eğitilmiş model yan açıda ve telefonda da çalışıyor.** Klasik POS burada büyük ölçüde başarısız (15.6 BPM).
  Hazır model 7.5 BPM'de kalıyor; ince ayarlı modeller 1.7–2.0 BPM'de.
- **Etiket temizliği bu testte fark yaratıyor.** Ana testte (önden webcam) 3 tur arasında fark yoktu:
  1.19 / 1.12 / 1.13. Burada 3. tur, takip edilmeden ölçülen argmax nabızda 1. tura göre %24 daha iyi
  (3.70 → 2.82). Video bazında 13 videoda daha iyi, 1 videoda daha kötü; 14 videoda fark ≤0.5 BPM.
- Bu beklenen bir sonuç: zaman kayması tam bu kameraların etiketlerindeydi (`VERI_KALITESI.md`).
- Viterbi takibi farkı daraltıyor (1.95 → 1.71), çünkü pencere hatalarının çoğunu zaten düzeltiyor.
- **En zor videolar:** 1097 (ana testte de en zoru), 1107 USB dinlenme, 1091 ve 1024 telefon dinlenme.
- **Sınırlar:**
  - 28 video, 10 kişiden geliyor ve aynı kişinin videoları birbirinden bağımsız değil.
  - "Telefon" burada Wi-Fi ile bilgisayara aktarılan bir telefon kamerası. Gerçek uygulama telefonun tarayıcısında
    ve farklı ışık koşullarında çalışıyor; bu test o koşulları tam temsil etmiyor.
