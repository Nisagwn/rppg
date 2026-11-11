# PURE eğitimi sonrası doğrulama ve sonraki koşular

11 Kasım 2026. İlk koşu: MMRPhys, PURE → UBFC, seed 42, sıfırdan eğitim.

## Tamamlananlar

- Kaggle çıktısı `results/derin_ogrenme/pure_weiqian_s1_seed42/` altında arşivlendi. Orijinal rapor ve günlükler korundu; `kaynak.json` arşiv/checkpoint SHA-256 değerlerini içerir.
- Eğitim 30 epoch. Eğitim: 9 PURE kişisinden 53 video; doğrulama: ayrı 1 kişiden 5 video. Depodaki 59 oturumdan biri yüz kalitesinde elendi. Orijinal rapordaki “58 video, 10 kişi” eğitim ve doğrulama girdilerinin toplamıdır.
- PURE doğrulama kişisine göre seçilen `best.pth`, epoch 2'dir. UBFC'nin 42 kişisinde pencere MAE 0.69 BPM, video MAE 0.89 BPM. `last.pth`: 0.74 / 1.35 BPM.
- ONNX adayı `mobile/model/mmrphys_pure_s1.onnx` olarak eklendi. Doğrulama: `onnx_dogrulama.json`; bir sabit tohumlu ve altı gerçek video parçası. Sayısal toleranslar raporda kayıtlıdır; en büyük nabız farkı yaklaşık 0.00163 BPM.
- Paketlenmiş mevcut ONNX'in tur5 checkpoint'iyle eşdeğerliği de aynı yedi girdide doğrulandı (`mevcut_onnx_dogrulama.json`). Adayın tarayıcı WASM/WebGPU çıktıları da karşılaştırıldı (`webgpu_dogrulama.json`): korelasyon yaklaşık 0.999999999. Bu WebGPU denemesi yazılım adaptöründedir; süreler fiziksel GPU/telefon performansı olarak kullanılmaz.
- Mevcut uygulama modeliyle aynı yerel test dosyalarında karşılaştırıldı: [çevrimdışı rapor](../results/derin_ogrenme/pure_weiqian_s1_seed42/karsilastirma/SONUCLAR.md).
- İki model aynı üç ham video kesitinde gerçek uygulama üzerinden yerel Chrome/WASM ile çalıştırıldı: [tarayıcı raporu](../results/mobil_pure_s1/SONUCLAR.md). Bu ölçüm masaüstündedir; telefon testi değildir.

## Model seçimi

Yeni adayın UBFC başarısı diğer kameralara aynı ölçüde taşınmadı. Aynı %50 örtüşme ve Viterbi ayarlarıyla:

| Yerel test | Video | PURE adayı MAE | Mevcut tur5 MAE |
|---|---:|---:|---:|
| Ana: 8 UBFC + 20 MCD webcam | 28 | 2.45 BPM | 1.10 BPM |
| MCD telefon / yan USB | 28 | 6.67 BPM | 1.59 BPM |

Kamera klasöründe 40 kayıt bulunur; 12'si ortak yüz kalitesi filtresinde elenir. Tablodaki 28, kalan gerçek test sayısıdır. Ana küme, ilk Kaggle değerlendirmesindeki 42 kişilik UBFC kümesiyle aynı değildir. Her tabloda yalnızca aynı kayıtlar üzerinde hesaplanan hatalar karşılaştırılır.

**Uygulamanın varsayılanı tur5 olarak korunur.** PURE modeli ayrı aday bağlantısındadır. Yerel tarayıcıda yeni model daha hızlı çalışsa da üç kesit tek kişidendir; buradan genel doğruluk veya telefon hızı sonucu çıkarılmaz.

- Mevcut: <https://nisagwn.github.io/rppg/?model=tur5>
- PURE adayı: <https://nisagwn.github.io/rppg/?model=pure>

Arka uç seçimi her model için ayrı saklanır. Eşit koşullu WASM testi için iki bağlantıya da `&ep=wasm` eklenebilir. Normal kullanımda uygulama desteklenen arka uçları kendi ölçerek seçer. Yeni sürüm v19; adayda “PURE S1” etiketi görünür. Model kimliği CSV, teşhis, ölçüm geçmişi ve `.rppgrec` başlığına eklenir.

## Telefonda oksimetreyle yapılacak ölçüm

Bu adım fiziksel telefon ve referans cihazla kullanıcı tarafından uygulanmalıdır; henüz tamamlanmış sayılmaz.

1. Aynı telefon, aynı kamera, aynı mesafe ve sabit ışıkla başlayın. Telefon/tarayıcı adı, tarih ve kullanılan bağlantıyı kaydedin.
2. Her iki model için ayrı oturumda “Veri kaydı (60 s)” kullanın. Önce sabit duruş; sonra hafif baş hareketi; sonra farklı ışıkta tekrarlayın. Model sırasını tekrarlar arasında değiştirin; her koşulu en az iki kez ölçün.
3. Oksimetre nabzını ölçümle eş zamanlı kaydedin; cihaz dalga/zaman serisi verebiliyorsa onu da saklayın. Tek bir son nabız değeri zaman içinde değişen gerçek dalga referansının yerini tutmaz.
4. Uygulamada oksimetre değerini girip Kaydet'e basın. Her oturumun CSV, teşhis JSON ve `.rppgrec` dosyalarını indirin. Güvenilmez/sonuç üretmeyen denemeleri de kaydedin; yalnızca iyi sonuçları seçmeyin.
5. CSV karşılaştırması `scripts/eval_app_csv.py` ile model bazında yapılır. Teşhis JSON'daki `model_ms`, arka uç, thread sayısı ve üretilen pencere sayısı birlikte değerlendirilir.

```powershell
.venv/Scripts/python.exe scripts/eval_app_csv.py kayit_tur5.csv kayit_pure.csv --hepsi
.venv/Scripts/python.exe scripts/import_own.py kayit.rppgrec --out data/dl/test_telefon --person p01
```

Yalnız oksimetre sayısıyla içe aktarılan kaydın etiketi `sabit_nabiz` olur ve eğitimde kullanılmaz. Gerçek PPG dalgası varsa `import_own.py --ppg ...` seçeneği zaman hizalamasıyla kullanılabilir. Kişisel kayıtlar `data/` altında kalır; Git'e eklenmez.

## S2 ve tohum tekrarları

Yeni defter: [rppg_standart_protokoller.ipynb](../kaggle/rppg_standart_protokoller.ipynb). GitHub URL'sini Kaggle Import Notebook alanına verin:

<https://github.com/Nisagwn/rppg/blob/main/kaggle/rppg_standart_protokoller.ipynb>

Varsayılan `DENEY="S2"`, `SEED=42`: UBFC'nin 42 kişisi kaynak, PURE hedef test kümesidir. Eğitim ve doğrulama kaynak içindeki ayrı kişilerden seçilir. PURE dosyaları eğitim köküne bağlanmaz. Hazır PURE ön-eğitimli model S2 kıyaslamasına eklenmez; hedefte önceden eğitim görmüş bir karşılaştırma bağımsız temel model sayılmaz.

Her çalıştırma tek protokol/tohumdur. Çıktı ve HF yedeği deney/tohum adıyla ayrılır; aynı ayarlarla yeniden başlatma aynı koşuya devam eder. Yapılacak koşular:

| Protokol | Tohum | Durum |
|---|---:|---|
| S1: PURE → UBFC | 42 | Tamamlandı, arşivlendi |
| S1 | 43 | Defter hazır; henüz çalıştırılmadı |
| S1 | 44 | Defter hazır; henüz çalıştırılmadı |
| S2: UBFC → PURE | 42 | Defterin varsayılanı; henüz çalıştırılmadı |
| S2 | 43 | Defter hazır; henüz çalıştırılmadı |
| S2 | 44 | Defter hazır; henüz çalıştırılmadı |

Bu bilgisayarda Kaggle API kimlik bilgisi bulunmadığından uzak GPU koşuları başlatılmadı. Kaggle Secrets değerleri burada okunmaz. Eğitim süresi 30 epoch, 500 adım, batch 8'dir. Aynı kişi ayrımı ve hiperparametreler tohumlar arasında sabit tutulur. Defter kaynak/hedef kişi ayrımını denetleyip `protokol.json` üretir.

İndirilen her `cikti/` klasörünü ayrı bir deney klasörüne açıp birleştirin:

```powershell
.venv/Scripts/python.exe scripts/summarize_protocol_seeds.py results/derin_ogrenme/pure_weiqian_s1_seed42 results/derin_ogrenme/s1_seed43 results/derin_ogrenme/s1_seed44 --out results/standart_tekrarlar
```

Mevcut `results/standart_tekrarlar/` yalnız S1/42'yi içerir. Tek tohumla standart sapma raporlanmaz. Bu araştırma protokolünün kırpma, nabız çıkarımı ve toplulaştırma ayarları farklı yayınlarla ayrıca eşleştirilmeden “literatürde en iyi” sonucu çıkarılmaz.

## Yerel kontrolleri tekrar çalıştırma

```powershell
.venv/Scripts/python.exe scripts/check_onnx_candidate.py
.venv/Scripts/python.exe scripts/compare_pure_candidate.py
.venv/Scripts/python.exe scripts/validate_pure_mobile.py
node mobile/test/webgpu_check.mjs --model pure
```

Karşılaştırma betikleri aynı işlenmiş veya ham dosyaların `data/` altında bulunmasını gerektirir. Raporlardaki masaüstü süreleri telefon ölçümü olarak kullanılmaz.
