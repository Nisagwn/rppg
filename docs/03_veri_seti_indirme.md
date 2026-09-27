# UBFC-rPPG Veri Setini İndirme

**Resmi sayfa:** https://sites.google.com/view/ybenezeth/ubfcrppg

## İçerik

- **DATASET_1 ("simple"):** 8 video, katılımcılar büyük ölçüde hareketsiz. Ground truth dosyası: `gtdump.xmp` (CSV; sütunlar: zaman (ms), HR, SpO2, PPG).
- **DATASET_2 ("realistic"):** 42 video. Katılımcılar HR'ı yükseltmek için zaman baskılı bir matematik oyunu oynuyor. Ground truth dosyası: `ground_truth.txt` (1. satır PPG, 2. satır HR, 3. satır zaman damgası).
- Çekim bilgileri: 640×480, 30 fps, sıkıştırılmamış 8-bit RGB, Logitech C920 kamera, CMS50E pulse oksimetre.
- Toplam boyut birkaç on GB olabilir. Önce 3–5 denek indirip deneyin.

## İndirme

**Otomatik (önerilen):** `CALISTIR.bat` → **D**, ya da

```
python scripts/download_ubfc.py --subjects 5                     # DATASET_2'den 5 denek
python scripts/download_ubfc.py --dataset DATASET_1 --subjects 0 # DATASET_1'in tamamı
```

Google Drive, çok indirilen dosyalarda geçici kota koyar ("Too many users have viewed or downloaded this file"). Bu durumda birkaç saat (en fazla 24 saat) sonra aynı komutu tekrar çalıştırın; inmiş dosyalar atlanır. Alternatif ayna: [Kaggle UBFC-rPPG](https://www.kaggle.com/datasets/malekdinarito/ubfc-rppg-dataset) (Kaggle hesabı gerekir).

> **Görüntü izni:** Veri setindeki `Agreement.xlsx` ve `readme.txt`'ye göre DATASET_2'de **subject21 ve subject27**'nin yüz görüntüleri hiçbir yayın, sunum veya raporda kullanılamaz.

**Elle:**

1. Resmi sayfadaki Google Drive bağlantısını açın.
2. `DATASET_2` klasöründen birkaç `subjectX` klasörü indirin.
3. İndirdiklerinizi şu yapıya yerleştirin:

```
rppg-projesi/
└── data/
    └── UBFC/
        └── DATASET_2/
            ├── subject1/
            │   ├── vid.avi
            │   └── ground_truth.txt
            ├── subject3/
            └── ...
```

4. Değerlendirmeyi çalıştırın:

```
python scripts/evaluate_ubfc.py --root data/UBFC --out results/ubfc
# hızlı deneme:
python scripts/evaluate_ubfc.py --root data/UBFC --max-subjects 3 --methods pos,chrom,green
```

İlk çalıştırmada her video bir kez işlenir; ROI izleri `results/ubfc/cache` klasöründe önbelleğe alınır. Sonraki çalıştırmalar birkaç saniye sürer.

## Atıf

> S. Bobbia, R. Macwan, Y. Benezeth, A. Mansouri, J. Dubois, "Unsupervised skin tissue segmentation for remote photoplethysmography", *Pattern Recognition Letters*, 2017/2019.

Veri seti yalnızca akademik kullanım içindir. Videoları başkalarıyla paylaşmayın.

## Derin Öğrenme Karşılaştırması (hibrit bölüm)

[rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox) (Liu vd., NeurIPS 2023), UBFC-rPPG için hazır yapılandırma dosyaları ve önceden eğitilmiş modeller (PhysNet, TS-CAN, DeepPhys, EfficientPhys, PhysFormer) içerir.

1. Toolbox'ı ayrı bir ortama kurun (PyTorch gerektirir). Toolbox README'si Windows'ta **WSL (Windows Subsystem for Linux)** kullanılmasını öneriyor:
   ```
   git clone https://github.com/ubicomplab/rPPG-Toolbox
   cd rPPG-Toolbox
   bash setup.sh conda        # veya: bash setup.sh uv
   ```
2. `configs/infer_configs/PURE_UBFC-rPPG_TSCAN_BASIC.yaml` dosyasını açın (PURE'de eğitilmiş, UBFC'de test edilen TS-CAN). `DATA_PATH` ve `CACHED_PATH` alanlarını kendi klasörünüze göre düzenleyin.
3. `python main.py --config_file ./configs/infer_configs/PURE_UBFC-rPPG_TSCAN_BASIC.yaml`
   Toolbox'ın kendi klasik yöntem uygulamalarıyla çapraz kontrol için `./configs/infer_configs/UBFC-rPPG_UNSUPERVISED.yaml` de çalıştırılabilir (bizim POS/CHROM sonuçlarımızla aynı büyüklükte çıkmalı).
4. Çıkan MAE, RMSE ve Pearson değerlerini `results/ubfc/SONUCLAR.md` ile aynı tabloya koyun. Raporun "Hibrit karşılaştırma" bölümü bu tablo üzerine yazılır.

> **Dikkat:** Toolbox varsayılan olarak video düzeyinde (tüm video FFT) değerlendirme yapar. Bu projenin tabloları hem pencere düzeyi (10 s) hem video düzeyi (`video_MAE`) sonuç verir. Karşılaştırmada **video_MAE** sütununu kullanın.
