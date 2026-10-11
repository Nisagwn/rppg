# Yerel eğitim, epoch 73 (durduruldu)

Bilgisayardaki ekran kartında (RTX 3050) yapılan ince ayar eğitiminin, aşırı ısınma nedeniyle durdurulduğu andaki hali.

- `best.pth`: epoch 72; doğrulama MAE 3.23 BPM.
- `gecmis.json`: 73 epoch'luk eğitim geçmişi.

Doğrulama kümesi eğitim sırasında değiştiği için bu değer `../egitim/` klasöründeki epoch 40 modelinin
(doğrulama 2.37) değeriyle doğrudan karşılaştırılamaz. Eğitim daha sonra Kaggle'da bu noktadan sürdürüldü
(1. tur: `../kaggle/`, defter kaydı: `kaggle/kayitlar/tur1_kaggle_ciktilari.ipynb`).
