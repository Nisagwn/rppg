# İş Planı — Derin Öğrenme Aşaması (Ekim 2026 – Şubat 2027)

Güncelleme: 12 Ekim 2026. Teslime ~4 ay var (Şubat 2027 ortası). Klasik yöntemler (POS, çoklu ROI, Viterbi, EVM,
sentetik benchmark) ve FactorizePhys ince ayarı tamamlandı. Bu aşamada **derin öğrenme projenin ana ekseni**.
Hedef: **MMRPhys modelini kendi veri setlerimizle sıfırdan eğitip** hatayı düşürmek ve telefonda çalıştırmak.

## Başlangıç noktası

| | Ana test (28 video, önden webcam) | Telefon/USB testi (28 video) |
|---|---:|---:|
| POS (klasik) + Viterbi | 3.54 BPM | 15.63 BPM |
| FactorizePhys hazır (PURE) + Viterbi | 2.57 BPM | 7.47 BPM |
| **FactorizePhys ince ayarlı (5. tur) + Viterbi** | **1.04 BPM** | **1.64 BPM** |

Hedef: iki testte de 5. turun altına inmek ve yeni telefon test kümelerinde (MMPD, VIPL-HR) ilk kez sonuç vermek.

## Neden MMRPhys

- Aynı ekibin (Joshi ve Cho, UCL) FactorizePhys'ten sonraki modeli (2025). Veri setleri arası testlerde
  FactorizePhys'ten daha iyi sonuç bildiriyor.
- Girdisi bizimkiyle aynı (72×72, 160 kare). Ön işleme değişmiyor.
- Daha küçük: 37.5 bin parametre (FactorizePhys 52 bin). İşlemcide 160 kare 0.13 s, telefona uygun.
- TSFM modülü etiketi yalnızca eğitimde kullanıyor. Kullanım anında sensör gerekmiyor (koddan doğrulandı).
- Hazır ağırlıkları mevcut koda tam oturmuyor. Sıfırdan eğitim zaten hedefimiz.
- Lisans: yalnızca araştırma amaçlı (RAIL). Bitirme projesi için uygun.

## Veri

| Veri seti | İçerik | Kaynak | Not |
|---|---|---|---|
| MCD-rPPG | 600 kişi, 3 kamera, dinlenme + egzersiz | HF `akramic/mcd_rppg` | Etiket ters işaretli; yan kameralarda zaman kayması düzeltildi |
| UBFC-rPPG | 42 kişi | HF `thachha901/UBFC` | 8 kişi testte |
| PURE | 10 kişi × 6 hareket | HF `Thinhnb29/PURE` | |
| UBFC-Phys | stres görevleri, bilek BVP | HF `jjuik2014/UBFC-Phys-all` | Video başına hizalama |
| **MMPD (mini)** | 33 kişi × 20 video, Samsung S22 Ultra | HF `WeiQian98/mini_MMPD` | Erişim onaylı. 80×60 çözünürlük |
| **VIPL-HR** | 107 kişi, webcam + RealSense + Huawei P9 | HF `WeiQian98/VIPL-HR` | Erişim onaylı. Bazı kaynaklarda zaman damgası yok |
| DLCN | 98 kişi, gece ışığı | Kaggle veri seti | |
| COHFACE | 40 kişi, yoğun sıkıştırma | HF `WeiQian98/COHFACE` | Muhtemelen çıkarılacak |

Test kişileri hiçbir eğitimde kullanılmaz. MMPD, VIPL-HR ve DLCN'de kişilerin %20'si ayrı test kümesi.

## 6. turdan çıkan dersler

- Defter 4.6 saatte hata vermeden durdu: RAM ya da disk doldu. Altı hazırlama süreci eğitimle aynı anda çalışıyordu.
  → **Hazırlama ve eğitim ayrı oturumlarda.**
- Veri geldikçe eğitim kaybı 0.36'dan 0.52'ye çıktı. Yeni veri setlerinde işaret ve zaman kayması hiç ölçülmemişti.
  → **Eğitimden önce kalite analizi.**
- Doğrulama yalnızca MCD ve UBFC'dendi; yeni verinin işe yarayıp yaramadığı görülemedi.
  → **Her veri setinden doğrulama videosu.**

## Haftalık plan

Kaggle GPU kotası haftada ~30 saat: haftada en fazla 2 tam eğitim.

| Hafta | Tarih | İş | Çıktı | Durum |
|---|---|---|---|---|
| **Aşama 1 — Veri** | | | | |
| 1 | 13–19 Eki | Kaggle'a `HF_TOKEN` + `HF_WRITE_TOKEN`. Yalnızca hazırlama yapan defter: her oturum bir-iki veri seti işler, sonucu HF'teki gizli `rppg-veri` deposuna yükler. İlk parça MMPD + VIPL-HR | `kaggle/hazirla.ipynb`; MMPD ve VIPL HF'te | ☐ |
| 2 | 20–26 Eki | Kalan parçalar (MCD iki oturumda, UBFC + PURE + UBFC-Phys, DLCN). Yeni veri setlerinde etiket kalitesi, işaret ve zaman kayması analizi; kayma tablosuna ekleme; kötü veri setlerini/videoları çıkarma | Tüm veri HF'te; `VERI_KALITESI.md` güncel | ☐ |
| **Aşama 2 — Altyapı** | | | | |
| 3 | 27 Eki–2 Kas | MMRPhys'i eğitim koduna bağlama (`--arch mmrphys`, rastgele başlatma seçeneği). Yalnızca eğitim yapan defter: veriyi HF'ten alır, her veri setinden doğrulama. Yerelde kısa deneme (RTX 3050). Erkenden ONNX dışa aktarma denemesi | `dl_train.py`, `kaggle/egit.ipynb`; MMRPhys ONNX'e çıkıyor mu | ☐ |
| **Aşama 3 — Ana deneyler** | | | | |
| 4 | 3–9 Kas | Deney A: FactorizePhys ince ayar, yeni veriyle (yeni verinin etkisi). Deney B: MMRPhys sıfırdan | 2 model + test sonuçları | ☐ |
| 5 | 10–16 Kas | Deney C: FactorizePhys sıfırdan (ön-eğitimin etkisi). Gerekirse B'nin devamı (sıfırdan eğitim daha uzun sürer) | 3 model karşılaştırması | ☐ |
| 6 | 17–23 Kas | Tüm modeller × tüm test kümeleri değerlendirme. Veri seti, kamera, ışık, hareket bazında hata analizi | `results/derin_ogrenme/karsilastirma/SONUCLAR.md` | ☐ |
| **Aşama 4 — Hatayı düşürme** | | | | |
| 7–9 | 24 Kas–14 Ara | Kazanan modelde iyileştirme turları (haftada 2 deney): veri artırma (telefon benzeri bozulma, ışık), öğrenme oranı/epoch, TSFM ayarları, kayıp fonksiyonu (Pearson + spektral), veri karışımı oranları | Her tur için tablo; en iyi model | ☐ |
| 10 | 15–21 Ara | İsteğe bağlı: solunum görevi (MMRPhys destekliyor; etiketli veri varsa). Yedek hafta | | ☐ |
| **Aşama 5 — Uygulama** | | | | |
| 11–12 | 22 Ara–4 Oca | En iyi modeli mobil uygulamaya taşıma (ONNX, `dl_worker.js`). Tarayıcı doğrulaması (`validate_mobile`, e2e). Telefonda hız ölçümü. Kendi kayıtlarımızla canlı deneme | Mobil v12 | ☐ |
| **Aşama 6 — Teslim** | | | | |
| 13–14 | 5–18 Oca | Sonuçları dondurma: son değerlendirme, Bland-Altman, tablolar ve grafikler | Son tablolar | ☐ |
| 15–17 | 19 Oca–8 Şub | Rapor (`05_rapor.md`) ve sunum. Derin öğrenme bölümü ana bölüm | Rapor, sunum | ☐ |
| 18 | 9–15 Şub | Yedek süre, prova, canlı demo testi | | ☐ |

## Deney tasarımı

Tüm deneyler aynı veri, aynı ön işleme ve aynı test kümeleriyle:

| | Hazır ağırlıktan | Sıfırdan |
|---|---|---|
| FactorizePhys | 5. tur (var) ve Deney A (yeni veri) | Deney C |
| MMRPhys | — | **Deney B (ana hedef)** |

- A ile 5. tur karşılaştırması → yeni verinin (telefon videoları) etkisi
- A ile C karşılaştırması → ön-eğitimin etkisi
- C ile B karşılaştırması → mimarinin etkisi

Test kümeleri: ana test (28), telefon/USB testi (28), MMPD testi, VIPL-HR testi, DLCN testi.
Ölçütler: MAE, RMSE, ≤5 BPM %, medyan, Pearson r, Bland-Altman; mobilde kare/s ve gecikme.

## Riskler

| Risk | Önlem |
|---|---|
| Kaggle oturumu yine çöker | Hazırlama ve eğitim ayrı; sonuçlar saatte bir HF'e yedeklenir; eğitim `last.pth`'den devam eder |
| Yeni veri setlerinde etiket sorunu | Eğitimden önce kalite analizi; düzeltilemeyen çıkarılır |
| MMRPhys daha iyi çıkmaz | Bu da bir sonuç: karşılaştırma raporlanır, en iyi model uygulamaya girer |
| Sıfırdan eğitim yavaş yakınsar | Daha uzun eğitim (200+ epoch, iki oturuma bölünür); öğrenme oranı denemesi |
| ONNX dışa aktarma ya da telefonda hız sorunu | 3. haftada erken deneme; gerekirse daha küçük MMRPhys çeşidi (36×36) |
| GPU kotası yetmez | Deney sırası önceliğe göre; yerel RTX 3050'de kısa denemeler |

## Kontrol Listesi (teslimden önce)

- [ ] Tüm tablolardaki sayılar son çalıştırmadan mı?
- [ ] Test kişileri hiçbir eğitimde kullanılmadı mı (kontrol betiği)?
- [ ] Kullanılan mimariler (FactorizePhys, MMRPhys) ve veri setleri kaynak gösterildi mi?
- [ ] Sentetik ve gerçek veri sonuçları ayrı ayrı ve açıkça etiketlendi mi?
- [ ] Bland-Altman grafiği var mı?
- [ ] Sınırlamalar bölümü dürüst mü (cilt tonu, hareket, referans cihaz hatası)?
- [ ] Katılımcı yüzleri yalnızca izin verenlerde mi kullanıldı?
- [ ] Kaynakça eksiksiz mi?
- [ ] Canlı demo sunum bilgisayarında ve telefonda test edildi mi (kamera izinleri, ışık)?
