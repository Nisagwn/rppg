# Eğitim Verisinin Etiket Kalitesi

Kaggle 2. turda eğitim kaybı 100 epoch boyunca 0.41–0.42'de kaldı ve doğrulama hatası başlangıç modelinden iyiye
gitmedi. Bu yüzden referans (sensör) sinyallerinin kalitesi ve görüntüyle zaman hizası ölçüldü.
Araç: `scripts/dl_quality.py` (ölçütler `scripts/dl_common.py: label_quality`), tablo: `kalite.csv`.

## Ölçütler

Her video 10 s pencerelere (2 s adım) bölündü:

- **Yalnızca etiketten:**
  - SNR: temel frekans ±6 BPM ve 1. harmonik ±12 BPM içindeki gücün geri kalan güce oranı.
  - Nabzın 40–180 BPM aralığında olması.
  - Komşu pencerelere göre 12 BPM'den büyük sıçrama olmaması.
  - Bu üç koşulu sağlayan pencere "iyi" sayıldı. Videonun yarısından fazlası kötüyse video atıldı. Kısmen kötü
    videolarda eğitim parçaları kötü bölümlerden seçilmiyor.
- **Etiket–görüntü uyumu:**
  - Yüz kırpıntısının ortasından POS sinyali çıkarıldı.
  - Etiketle POS arasındaki korelasyon ±1 s gecikme aralığında hesaplandı.
  - İki sinyalden ayrı ayrı bulunan nabızların ne kadar örtüştüğü ölçüldü.

## Bulgular

### 1. MCD yan kameralarında etiket zaman kayması (asıl sorun)

MCD'de her oturum üç kamerayla kayıtlı ve hepsinde aynı parmak sensörü kullanılıyor. Aynı oturumun önden ve yan
kamera etiketlerinden çıkan nabız %100 aynı. Ancak POS–etiket korelasyonu, her kamera için 150 videonun ortalama
eğrisinde farklı gecikmelerde tepe yapıyor:

| Kamera | Tepe gecikmesi | Önden webcam'e göre | Gecikme 0'da r |
|---|---:|---:|---:|
| FullHDwebcam (önden) | −3 kare | – | +0.30 |
| IriunWebcam (telefon, Wi-Fi) | −7 kare | 4 kare (~130 ms) | **−0.12** |
| USBVideo | −11 kare | 8 kare (~270 ms) | **−0.26** |

- 270 ms yaklaşık yarım nabız periyodu. Bu yüzden **USB videolarında etiket görüntüye göre fiilen ters işaretliydi.**
- 1. ve 2. turlarda MCD eğitim videolarının ~%60'ı (Iriun 1016 ve USB 585 video) bu kaymayla eğitildi. Model,
  videonun yarısında doğru dalgayı, diğer yarısında gecikmiş ya da ters dalgayı öğrenmeye zorlandı.
- **Düzeltme:** etiketler Iriun'da 4, USB'de 8 kare geciktiriliyor (`CAMERA_SHIFT`). Düzeltmeden sonra her iki
  kameranın ortalama eğrisi de önden webcam gibi −3 karede tepe yapıyor; gecikme 0'daki r değeri +0.14 / +0.15.
- Önden webcam'deki −3 kare (~100 ms) beklenen bir fark: parmak nabzı yüze göre geç gelir. Test etiketleri de bu
  hizada olduğundan referans olarak bu alındı.

### 2. POS uyumu yan kameralarda etiket ölçütü olarak kullanılamaz

Yan kameralarda POS nabzı etiketle %22–39 örtüşüyor. Ancak aynı oturumun önden kamerasındaki POS ile de yalnızca
%22–28 örtüşüyor; oysa etiketler aynı. Yani sorun etikette değil, POS'un yan açıdan nabzı bulamamasında. Bu ölçüt
filtre olarak kullanılsaydı zor ama geçerli videolar atılırdı, bu yüzden kullanılmadı.

### 3. UBFC-Phys (2. tur günlüğünden)

- Bilek sensörü (Empatica E4). Hizalama ve işaret kişiden kişiye değişiyor: dinlenme görevinde s18 için r = +0.86,
  s19 için −0.71, s20 için +0.73.
- Konuşma ve aritmetik görevlerinde ortalama |r| 0.10–0.11; etiket görüntüyle neredeyse hiç örtüşmüyor.
- 2. turda tek bir işaret kararıyla (oylama) eğitildi.
- **Düzeltme:** her video ±1 s içinde ayrı ayrı hizalanıyor; hizalandığında bile r < 0.4 kalan videolar atılıyor.

### 4. Etiketin kendisi kötü olan videolar

| Veri | Video | Atılan | Ortalama iyi pencere |
|---|---:|---:|---:|
| MCD | 2695 | 51 | %94 |
| UBFC | 34 | 0 | %97 |
| PURE | 58 | 0 | %98 |

### 5. Test kümesi

- **UBFC subject4:** referans sinyalin yalnızca %39'u iyi (SNR −0.4 dB).
- **UBFC subject3:** referans sinyalin %57'si iyi (SNR 1.8 dB).

Bu iki video 1. ve 2. turda en yüksek hatalı test videolarıydı; hatanın bir kısmı referansın kendisinden geliyor.
Ana tabloda yine de 28 videonun tamamı kullanılıyor. `dl_evaluate.py` ayrıca referansı temiz videolarla ek bir
tablo yazıyor.

MCD 1097'nin etiketi temiz (SNR 7.6–9.1 dB), ama POS da bu kişide başarısız. Etiket hatası kanıtlanmadı; zor bir
video olarak kalıyor.

## 3. tur

`kaggle/rppg_egitim_3.ipynb`: 2. turla aynı başlangıç modeli, veri ve ayarlar kullanılıyor; tek fark yukarıdaki
temizlik. Karşılaştırma aynı 28 test videosunda, 1. ve 2. tur modelleri de yan yana ölçülerek yapılıyor.
