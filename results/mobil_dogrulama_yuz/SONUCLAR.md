# Mobil Uygulama — Gerçek Veri Doğrulaması

Her kesit (40 s) Chrome'a sahte kamera olarak verildi; uygulama tarayıcıda gerçek zamanlı ölçtü. Referans: parmak PPG'sinden 10 s pencere başına spektral tepe. İlk 10 s (ısınma) hariç.

## Yüz dedektörü: teşhis ve karma dedektör (v13)

**Teşhis (v12, yalnızca pico; `results/mobil_dogrulama_yuz_pico/`, `?yuz=pico`).** Uygulamaya saniyelik teşhis kaydı
eklendi (`window.__rppg.diag`: kare sayısı, yüz kutusu olan kare, tespit denemesi/başarısı, ölçümün durduğu yer).
Uygulamada SNR'ye bağlı bir sonuç kapısı yok (SNR yalnızca durum yazısını belirler); ölçüm üç yerde durabiliyor:
yüz kutusu olan kare < %70 (`yuz_yok`), geçerli veri < 8 s (`isinma`), modelin birleşik dalgası < 8 s (`model_isinma`;
5.3 s'lik model penceresinde 0.35 s'den uzun kare boşluğu olunca pencere atlanıyor). v12'de sonuçsuz 20 kesitte
(t ≥ 10 s) ölçümsüz saniyelerin %81'i (437 s) **yüz bulunamadı**, %11'i (57 s) model ısınması, %2'si (13 s) ısınma;
16/20 kesitte yüzlü kare oranı < %30 (USB kesitlerinin 9'unda %0). Kalan 4 telefon kesitinde yüz %76–85 bulunuyor
ama aralıklı kayıplar model penceresini bölüyor (yine dedektör kaynaklı). Çevrimdışı pico denemesi (dökülmüş 480x360
gri kareler, uygulamanın mantığıyla; 29 kesit) aynı sonucu verdi: USB'de pico puanı medyan 0–3 (eşik 50).

**pico parametreleri (çevrimdışı, 29 kesit, yüzlü kare oranı önden / telefon / USB):** varsayılan 100 / 57 / 25;
eşik q>20: 100 / 90 / 42; q>5: 100 / 99 / 61 (yanlış tespit riski); ince tarama (kaydırma 0.05, ölçek 1.05,
~2.3x süre): 100 / 99 / 43; en küçük yüz 0.05: 100 / 57 / 21; ±20° döndürülmüş tarama (3x süre): 100 / 62 / 39;
5→10 kare bellek + 3 s tutma: 100 / 86 / 41. Hiçbiri USB'yi kurtarmıyor (9/15 kesit hâlâ < %70).

**Çözüm: YuNet** (Wu vd. 2023; OpenCV Zoo `face_detection_yunet_2026may.onnx`, 230 KB, MIT lisansı,
`mobile/vendor/yunet/LICENSE`), mevcut onnxruntime-web ile ayrı Worker'da (`face_worker.js`, wasm, tek iş parçacığı,
GPU yok). Python'da (onnxruntime, aynı kod çözme) 60 kesitin tamamında karelerin ≥ %99.3'ünde yüz buldu (256 px girdide
de zor 8 kesitte %100). YuNet kutusu pico kutusuna, ikisinin birlikte bulduğu 1500 önden karede öğrenilen doğrusal
eşlemeyle çevrilir (merkez −0.024·w, −0.051·h; kenar 1.114·√(w·h); eşleme sonrası merkez farkı kutunun %3'ü, boyut
oranı 1.00, p10–p90 0.94–1.07), böylece ROI kesirleri ve modelin x1.5 kırpması değişmez. Yan açıda ROI'ler görsel
olarak yüzde kalıyor. **Karma dedektör:** önce pico; bulamazsa YuNet; pico art arda 3 kez kaçırırsa 3 s atlanır.
Önden kamerada YuNet hiç devreye girmedi (pico 5034 / YuNet 0 tespit), telefonda tespitlerin %32'si, USB'de %70'i
YuNet'ten; YuNet süresi masaüstünde medyan 6–7 ms (256x192 girdi).

| koşu | kamera | kapsama % | sonuçsuz kesit | MAE (pencere veren kesitler) |
|:--|:--|--:|--:|--:|
| v12 (pico) | önden / telefon / USB | 81 / 48 / 23 | 0 / 7 / 13 | 3.24 / 2.31 / 4.41 |
| v13 karma | önden / telefon / USB | 93 / 95 / 94 | 0 / 0 / 0 | 3.59 / 3.70 / 2.85 |

Eşleştirilmiş Wilcoxon (v12 → v13): her iki koşuda da pencere veren kesitlerde MAE önden 3.24 → 3.59 (n=20, p=0.62),
telefon 2.31 → 2.12 (n=13, p=0.59), USB 4.41 → 2.06 (n=7, p=0.22), tümü 3.14 → 2.85 (n=40, p=0.17): doğruluk
anlamlı değişmedi. Kesit başına pencere sayısı: telefon 11.9 → 23.8 (p=0.001), USB 5.8 → 23.6 (p=0.0001),
önden 20.2 → 23.4 (p=0.06). Yeni ölçülen 20 kesitte MAE: USB 13 kesit 3.28 (≤5 BPM %83), telefon 7 kesit 6.64
(%66; 1097 ve 1113 kişileri zor).

Notlar: (1) Koşular aynı makinede başka bir ajanın tarayıcı testleriyle eşzamanlı yapıldı; yük altında tarayıcı
kare hızı düştüğünde `model_isinma` artıyor. Aynı oturumdaki pico koşusu daha yüklü saatlere denk geldi (önden
MAE 5.70), bu yüzden temel çizgi olarak v12 kullanıldı; önden kamerada dedektör v12 ile birebir aynı (YuNet
çağrılmıyor), farklar yükten. (2) Chrome `--disable-gpu` ile çalıştı (yazılım WARP), ONNX yalnızca wasm.
(3) Önden kapsama artışı (81 → 93) dedektörden değil, daha az yüklü makineden.

## Karşılaştırma tabloları (`scripts/compare_mobile_face.py`)

### Kamera başına

| koşu | kamera | kesit | kapsama % | sonuçsuz kesit | MAE (pencere veren kesitler) | ≤5 BPM % |
|:--|:--|--:|--:|--:|--:|--:|
| mobil_dogrulama_v12 | webcam (önden) | 20 | 81 | 0 | 3.24 | 86 |
| mobil_dogrulama_v12 | telefon | 20 | 48 | 7 | 2.31 | 89 |
| mobil_dogrulama_v12 | USB (yan) | 20 | 23 | 13 | 4.41 | 84 |
| mobil_dogrulama_v12 | tümü | 60 | 51 | 20 | 3.14 | 87 |
| mobil_dogrulama_yuz_pico | webcam (önden) | 20 | 73 | 0 | 5.70 | 77 |
| mobil_dogrulama_yuz_pico | telefon | 20 | 43 | 6 | 3.83 | 82 |
| mobil_dogrulama_yuz_pico | USB (yan) | 20 | 15 | 14 | 1.96 | 97 |
| mobil_dogrulama_yuz_pico | tümü | 60 | 44 | 20 | 4.48 | 82 |
| mobil_dogrulama_yuz | webcam (önden) | 20 | 93 | 0 | 3.59 | 82 |
| mobil_dogrulama_yuz | telefon | 20 | 95 | 0 | 3.70 | 84 |
| mobil_dogrulama_yuz | USB (yan) | 20 | 94 | 0 | 2.85 | 87 |
| mobil_dogrulama_yuz | tümü | 60 | 94 | 0 | 3.38 | 84 |

### Teşhis: ölçümsüz saniyelerin nedeni (t ≥ 10 s, kamera başına toplam)

| koşu | kamera | yüz kutusu olan kare % | yüz yok (s) | ısınma (s) | model ısınma (s) | ölçüm (s) |
|:--|:--|--:|--:|--:|--:|--:|
| mobil_dogrulama_yuz_pico | webcam (önden) | 100 | 0 | 1 | 154 | 365 |
| mobil_dogrulama_yuz_pico | telefon | 80 | 114 | 12 | 176 | 216 |
| mobil_dogrulama_yuz_pico | USB (yan) | 42 | 323 | 4 | 127 | 75 |
| mobil_dogrulama_yuz | webcam (önden) | 100 | 0 | 2 | 78 | 467 |
| mobil_dogrulama_yuz | telefon | 100 | 0 | 0 | 76 | 476 |
| mobil_dogrulama_yuz | USB (yan) | 100 | 0 | 0 | 82 | 472 |

### Eşleştirilmiş karşılaştırma (iki koşuda da pencere veren kesitler, kesit MAE'si)

| A | B | kamera | n | MAE A | MAE B | Wilcoxon p | pencere A | pencere B | Wilcoxon p (pencere, tüm kesitler) |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|
| mobil_dogrulama_v12 | mobil_dogrulama_yuz_pico | webcam (önden) | 20 | 3.24 | 5.70 | 0.409 | 20.2 | 18.2 | 0.6469 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz_pico | telefon | 13 | 2.31 | 4.05 | 0.542 | 11.9 | 10.8 | 0.4413 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz_pico | USB (yan) | 5 | 3.48 | 2.19 | 0.812 | 5.8 | 3.8 | 0.2328 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz_pico | tümü | 38 | 2.95 | 4.67 | 0.473 | 12.6 | 10.9 | 0.2037 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz | webcam (önden) | 20 | 3.24 | 3.59 | 0.622 | 20.2 | 23.4 | 0.0600 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz | telefon | 13 | 2.31 | 2.12 | 0.588 | 11.9 | 23.8 | 0.0011 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz | USB (yan) | 7 | 4.41 | 2.06 | 0.219 | 5.8 | 23.6 | 0.0001 |
| mobil_dogrulama_v12 | mobil_dogrulama_yuz | tümü | 40 | 3.14 | 2.85 | 0.170 | 12.6 | 23.6 | 0.0000 |
| mobil_dogrulama_yuz_pico | mobil_dogrulama_yuz | webcam (önden) | 20 | 5.70 | 3.59 | 0.076 | 18.2 | 23.4 | 0.0025 |
| mobil_dogrulama_yuz_pico | mobil_dogrulama_yuz | telefon | 14 | 3.83 | 2.01 | 0.426 | 10.8 | 23.8 | 0.0001 |
| mobil_dogrulama_yuz_pico | mobil_dogrulama_yuz | USB (yan) | 6 | 1.96 | 1.90 | 1.000 | 3.8 | 23.6 | 0.0001 |
| mobil_dogrulama_yuz_pico | mobil_dogrulama_yuz | tümü | 40 | 4.48 | 2.78 | 0.068 | 10.9 | 23.6 | 0.0000 |

## Özet

| kaynak   | kamera         | durum            |   kesit |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |
|:---------|:---------------|:-----------------|--------:|---------------:|------------------:|-------------:|
| MCD      | USB (yan)      | dinlenme         |      10 |           2.94 |             86.85 |        14.67 |
| MCD      | USB (yan)      | egzersiz sonrası |      10 |           2.77 |             86.83 |        20.73 |
| MCD      | telefon        | dinlenme         |      10 |           3.96 |             83.46 |        12.38 |
| MCD      | telefon        | egzersiz sonrası |      10 |           3.44 |             84.43 |         8.3  |
| MCD      | webcam (önden) | dinlenme         |      10 |           3.89 |             80.84 |         4.49 |
| MCD      | webcam (önden) | egzersiz sonrası |      10 |           3.3  |             83.95 |         8.29 |

**Genel:** uygulama MAE 3.38 BPM, pencerelerin %84'i ≤5 BPM; aynı kesitlerde Python hattı MAE 11.10 BPM (60 kesit).

## Kesitler

| kaynak   | ad                       | kamera         | durum            |   pencere |   uygulama_MAE |   uygulama_≤5BPM% |   python_MAE |   referans_ort |   yuz_kare% |   tespit% |   sn_yuz_yok |   sn_isinma |   sn_model_isinma |   sn_olcum |
|:---------|:-------------------------|:---------------|:-----------------|----------:|---------------:|------------------:|-------------:|---------------:|------------:|----------:|-------------:|------------:|------------------:|-----------:|
| MCD      | 1020_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        23 |           2.7  |             86.96 |         0.58 |          77.5  |      100    |    100    |            0 |           0 |                 3 |         23 |
| MCD      | 1020_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           4.15 |             76    |        10.09 |          77.5  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1020_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           3.55 |             80    |         8.49 |          77.51 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1020_FullHDwebcam_before | webcam (önden) | dinlenme         |        21 |           1.59 |             95.24 |         0.73 |          75.37 |      100    |    100    |            0 |           0 |                 3 |         21 |
| MCD      | 1020_USBVideo_before     | USB (yan)      | dinlenme         |        16 |           1.56 |             93.75 |         4.74 |          75.37 |       99.42 |    100    |            0 |           0 |                12 |         16 |
| MCD      | 1020_IriunWebcam_before  | telefon        | dinlenme         |        25 |           1.82 |             96    |         1.14 |          75.37 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1024_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        24 |           1.55 |            100    |         1.23 |          69.16 |      100    |    100    |            0 |           0 |                 3 |         24 |
| MCD      | 1024_USBVideo_after      | USB (yan)      | egzersiz sonrası |        24 |           1.86 |             95.83 |        22.21 |          69.16 |      100    |    100    |            0 |           0 |                 4 |         24 |
| MCD      | 1024_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.6  |            100    |        13.11 |          69.16 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1024_FullHDwebcam_before | webcam (önden) | dinlenme         |        24 |           1.39 |            100    |         0.73 |          74.74 |      100    |    100    |            0 |           0 |                 4 |         24 |
| MCD      | 1024_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           1.52 |            100    |         1.18 |          74.75 |      100    |    100    |            0 |           0 |                 3 |         26 |
| MCD      | 1024_IriunWebcam_before  | telefon        | dinlenme         |        20 |           2.92 |            100    |        18.91 |          74.75 |      100    |    100    |            0 |           0 |                 6 |         20 |
| MCD      | 1035_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        16 |           3.26 |             75    |         0.76 |          74.39 |      100    |    100    |            0 |           1 |                 7 |         16 |
| MCD      | 1035_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           2.25 |             88    |         3.11 |          74.38 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1035_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.93 |            100    |         4.67 |          74.38 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1035_FullHDwebcam_before | webcam (önden) | dinlenme         |        23 |           1.38 |            100    |         1.54 |          68.91 |      100    |    100    |            0 |           0 |                 5 |         23 |
| MCD      | 1035_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           1.21 |            100    |         3.6  |          68.9  |      100    |     99.46 |            0 |           0 |                 3 |         25 |
| MCD      | 1035_IriunWebcam_before  | telefon        | dinlenme         |        18 |           1.49 |            100    |         3.7  |          68.91 |      100    |    100    |            0 |           0 |                11 |         18 |
| MCD      | 1091_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           1.53 |             96    |         0.46 |         102.47 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1091_USBVideo_after      | USB (yan)      | egzersiz sonrası |        24 |           2.18 |             87.5  |        39.76 |         102.49 |      100    |    100    |            0 |           0 |                 4 |         24 |
| MCD      | 1091_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.4  |            100    |        15.71 |         102.49 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1091_FullHDwebcam_before | webcam (önden) | dinlenme         |        24 |          11.47 |             29.17 |         0.69 |          85.76 |      100    |    100    |            0 |           0 |                 4 |         24 |
| MCD      | 1091_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           1.61 |            100    |        19.63 |          85.76 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1091_IriunWebcam_before  | telefon        | dinlenme         |        23 |           2.24 |             78.26 |        10.64 |          85.76 |      100    |    100    |            0 |           0 |                 5 |         23 |
| MCD      | 1097_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        23 |           3.45 |             82.61 |        17.7  |          88.71 |      100    |    100    |            0 |           0 |                 5 |         23 |
| MCD      | 1097_USBVideo_after      | USB (yan)      | egzersiz sonrası |        20 |           5.15 |             65    |         5.16 |          88.7  |      100    |    100    |            0 |           0 |                 6 |         20 |
| MCD      | 1097_IriunWebcam_after   | telefon        | egzersiz sonrası |        24 |          15.34 |              8.33 |        10.33 |          88.71 |      100    |    100    |            0 |           0 |                 4 |         24 |
| MCD      | 1097_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           6.46 |             72    |        31.68 |          93.71 |      100    |    100    |            0 |           1 |                 3 |         25 |
| MCD      | 1097_USBVideo_before     | USB (yan)      | dinlenme         |        18 |           9.42 |             38.89 |        40.6  |          93.7  |      100    |     99.38 |            0 |           0 |                 8 |         18 |
| MCD      | 1097_IriunWebcam_before  | telefon        | dinlenme         |        22 |          15.51 |             36.36 |        34.68 |          93.69 |      100    |    100    |            0 |           0 |                 4 |         22 |
| MCD      | 1099_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        18 |          11.83 |             38.89 |         1.01 |          86.37 |      100    |    100    |            0 |           0 |                10 |         18 |
| MCD      | 1099_USBVideo_after      | USB (yan)      | egzersiz sonrası |        21 |           2.09 |            100    |        23.92 |          86.37 |      100    |    100    |            0 |           0 |                 6 |         21 |
| MCD      | 1099_IriunWebcam_after   | telefon        | egzersiz sonrası |        19 |           1.83 |            100    |         8.21 |          86.37 |      100    |    100    |            0 |           0 |                 4 |         19 |
| MCD      | 1099_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           2.71 |             76    |         1.46 |          74.33 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1099_USBVideo_before     | USB (yan)      | dinlenme         |        24 |           1.96 |             95.83 |         9.14 |          74.36 |      100    |    100    |            0 |           0 |                 3 |         24 |
| MCD      | 1099_IriunWebcam_before  | telefon        | dinlenme         |        25 |           2.96 |             80    |         8.26 |          74.34 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1107_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        21 |           1.51 |            100    |        57.89 |         123.71 |      100    |    100    |            0 |           0 |                 4 |         21 |
| MCD      | 1107_USBVideo_after      | USB (yan)      | egzersiz sonrası |        24 |           0.95 |            100    |        53.89 |         123.7  |      100    |    100    |            0 |           0 |                 3 |         24 |
| MCD      | 1107_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           1.11 |            100    |         3.07 |         123.7  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1107_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           2.12 |             88    |         1    |          89.41 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1107_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           2.31 |             92    |         7.39 |          89.42 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1107_IriunWebcam_before  | telefon        | dinlenme         |        25 |           2.1  |             92    |        24.65 |          89.4  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           3.67 |             76    |         1.61 |          82.67 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           5.25 |             72    |       nan    |          82.1  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           4.52 |             68    |         6.98 |          82.66 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           4.71 |             80    |         1.17 |          83.51 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           4.02 |             72    |        41.47 |          83.52 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1113_IriunWebcam_before  | telefon        | dinlenme         |        25 |           4.19 |             80    |        12.45 |          83.51 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1115_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           2.81 |             84    |         1.21 |          92    |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1115_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           2.92 |             84    |       nan    |          92.04 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1115_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           2.57 |             88    |        11.36 |          92.02 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1115_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           6.45 |             68    |         5.5  |          75.51 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1115_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           5.13 |             76    |       nan    |          75.48 |      100    |     99.52 |            0 |           0 |                 3 |         25 |
| MCD      | 1115_IriunWebcam_before  | telefon        | dinlenme         |        25 |           5.8  |             72    |         8.23 |          75.51 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_FullHDwebcam_after  | webcam (önden) | egzersiz sonrası |        25 |           0.66 |            100    |         0.4  |          67.3  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_USBVideo_after      | USB (yan)      | egzersiz sonrası |        25 |           0.86 |            100    |         7.71 |          67.3  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_IriunWebcam_after   | telefon        | egzersiz sonrası |        25 |           0.54 |            100    |         1.02 |          67.3  |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_FullHDwebcam_before | webcam (önden) | dinlenme         |        25 |           0.65 |            100    |         0.43 |          71.36 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_USBVideo_before     | USB (yan)      | dinlenme         |        25 |           0.7  |            100    |         4.32 |          71.36 |      100    |    100    |            0 |           0 |                 3 |         25 |
| MCD      | 1149_IriunWebcam_before  | telefon        | dinlenme         |        25 |           0.56 |            100    |         1.19 |          71.37 |      100    |    100    |            0 |           0 |                 3 |         25 |
