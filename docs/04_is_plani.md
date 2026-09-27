# İş Planı (12 hafta)

Kod altyapısı hazır. Plan, **deneyleri gerçek veride yürütmeye, kendi veri setini toplamaya ve raporu yazmaya** göre ayarlanmıştır.

| Hafta | İş | Çıktı | Durum |
|---|---|---|---|
| 1 | Literatür okuma (Verkruysse, Poh, de Haan, Wang, Wu); kurulum; sentetik demoyu çalıştırma | Okuma notları | ☐ |
| 2 | Kod tabanını anlama: `roi.py` → `signals.py` → `methods.py` → `hr.py`; testleri çalıştırma | Her modül için 3–4 cümle açıklama | ☐ |
| 3 | UBFC indirme (3–5 denek); `evaluate_ubfc.py` ile ilk sonuçlar | İlk MAE tablosu | ☑ 8 denek |
| 4 | UBFC tamamı; yöntem × ROI × füzyon × takip ablasyonu | `results/ubfc/SONUCLAR.md` | ◐ ablasyon 8 denekte; tamamı için `download_ubfc.py --subjects 0` |
| 5 | Onam formları; ekipman (oksimetre); pilot kayıt (kendin) | Protokol test edildi | ☐ |
| 6–7 | 5–10 katılımcı × 7 koşul kayıt | `data/kayitlar/` | ☐ |
| 8 | Kendi verisinde analiz: koşul × yöntem tablosu | Koşul ısı haritası | ◐ ekipman yokken MCD-rPPG ile (kamera × dinlenme/egzersiz): `results/mcd/` |
| 9 | Hibrit: rPPG-Toolbox derin modelleri ile UBFC karşılaştırması | Karşılaştırma tablosu | ☐ |
| 10 | EVM videoları, canlı demo iyileştirme, ekran kayıtları | Demo videosu | ☐ |
| 11 | Rapor yazımı (`05_rapor.md` taslağını gerçek sonuçlarla doldur) | Rapor v1 | ☐ |
| 12 | Sunum ve prova; canlı demo | Sunum | ☐ |

## Kontrol Listesi (teslimden önce)

- [ ] Tüm tablolardaki sayılar son çalıştırmadan mı?
- [ ] Sentetik ve gerçek veri sonuçları ayrı ayrı ve açıkça etiketlendi mi?
- [ ] Bland-Altman grafiği var mı?
- [ ] Sınırlamalar bölümü dürüst mü (cilt tonu, hareket, referans cihaz hatası)?
- [ ] Katılımcı yüzleri yalnızca izin verenlerde mi kullanıldı?
- [ ] Kaynakça eksiksiz mi?
- [ ] Canlı demo sunum bilgisayarında test edildi mi (kamera izinleri, ışık)?
