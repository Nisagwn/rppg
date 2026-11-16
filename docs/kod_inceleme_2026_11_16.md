# Kod inceleme raporu — 16 Kasım 2026

İncelenen sürüm: [`8f07cca`](https://github.com/Nisagwn/rppg/commit/8f07ccac2a04f053f626d05238b933838104f361).
Kapsam: telefon kayıtlarının içe aktarılması, referans ölçüm istatistikleri ve mevcut Python/mobil testleri.
Bu bir tam depo denetimi değildir. **Bu çalışmada uygulama veya betik kodu değiştirilmedi; yalnız bu rapor eklendi.**

## Bulgular

P2: normal öncelikli işlev/veri doğruluğu hatası. P3: daha düşük öncelikli dosya doğrulama hatası.
İlk dört davranış bulgusu yerel örneklerle yeniden üretildi; pandas uyumsuzluğu kaynak kodu ve resmî API belgesiyle doğrulandı.

### 1. [P2] Başlıksız PPG CSV'sinin ilk örneği kayboluyor

**Yer:** [`scripts/import_own.py:47–51`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/import_own.py#L47-L51).

`read_ppg` açıklaması başlığın isteğe bağlı olduğunu söylüyor; fakat `pd.read_csv(path)` ilk satırı her zaman sütun başlığı kabul ediyor.
Üç sayısal satırla yapılan kontrolde iki örnek döndü. İlk zaman damgası `1700000000000` yerine `1700000000017` oldu.

**Etki:** Başlıksız oksimetre kaydında ilk veri sessizce atlanır. Video aynı ilk örnek anında başlıyorsa, `main` içindeki kapsam kontrolü de PPG'nin videoyu kapsamadığını söyleyerek içe aktarmayı durdurabilir.

**Beklenen:** Başlıklı ve başlıksız dosyalar ayırt edilmeli; başlıksız dosyada ilk sayısal satır korunmalı.

### 2. [P2] Sırasız PPG zaman damgaları yanlış etiket üretmesine rağmen kabul ediliyor

**Yer:** [`scripts/import_own.py:47–51`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/import_own.py#L47-L51), [`71–75`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/import_own.py#L71-L75).

Okuyucu zaman sırasını denetlemiyor. `main` yalnız başlangıç/bitiş kapsamını kontrol edip aynı diziyi `np.interp` çağrısına veriyor.
Başlıklı bir CSV'de zaman/değer çiftleri `(0,0), (2000,100), (1000,10), (3000,20)` olduğunda 1500 ms'deki değer **75** çıkıyor.
Çiftler zaman sırasına konulduğunda doğru doğrusal ara değer **55**. İlk ve son zamanlar uygun olduğundan mevcut kapsam kontrolü bu örneği yakalamıyor.

**Etki:** Sırası bozuk bir sensör CSV'si kullanılırsa yanlış PPG dalgası `label="dalga"` olarak eğitim girdisine kaydedilebilir. Bu rapor, mevcut eğitim verilerinde böyle bir dosya bulunduğu iddiasında değildir.

**Beklenen:** Enterpolasyondan önce zamanların artışı doğrulanmalı; sırasız veya yinelenen zamanlar açık bir kuralla ele alınmalı ya da açıklayıcı hatayla reddedilmeli.

### 3. [P2] Eksik ölçümler örnek sayısı ve başarı oranında tutarsız sayılıyor

**Yer:** [`scripts/eval_app_csv.py:36–41`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/eval_app_csv.py#L36-L41).

İki satırlı referans tablosunda bir satır `uygulama_bpm=72, cihaz_bpm=74`, diğer satır ise boş `uygulama_bpm` ve `cihaz_bpm=74` içerdiğinde sonuç:

| Ölçüt | Gözlenen |
|---|---:|
| `n` | 2 |
| MAE | 2 BPM |
| ±5 BPM içinde | %50 |

MAE hesabı NaN satırı atlayıp bir ölçümü kullanıyor. Başarı oranında `NaN <= 5` yanlış sayıldığı için iki satır kullanılıyor; `n` de iki gösteriliyor.

**Etki:** Eksik/değiştirilmiş bir CSV rapora girerse aynı tablonun ölçütleri farklı geçerli örnek sayılarına dayanır. Normal uygulama çıktısında boş satır oluştuğu bu incelemede gösterilmedi; hata, okuyucunun kabul ettiği bu girdide yeniden üretildi.

**Beklenen:** Geçerli ölçüm çifti sayısı ve eksik ölçüm sayısı ayrılmalı. Eksik sonuçlar kapsama ölçütünde tutulacaksa, MAE'nin örnek sayısı ayrıca belirtilmeli.

### 4. [P3] `.rppgrec` sonundaki eksik kare parçası sessizce atılıyor

**Yer:** [`scripts/import_own.py:39–44`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/import_own.py#L39-L44).

Kare sayısı tam bölmeyle hesaplanıyor; kalan bayt sayısı kontrol edilmiyor. Başlığında iki kare yazan, iki tam `72×72×3` kare ve fazladan bir bayt içeren dosya hatasız okunuyor. Son bayt dilimleme sırasında atılıyor.

**Etki:** Bildirilen kare sayısı doğru olsa bile dosyanın beklenen gövde uzunluğuna uymadığı fark edilmiyor. Bu, mevcut indirmelerin bozuk olduğunu göstermez; örnek dosyada bozuk gövdenin kabul edildiğini gösterir.

**Beklenen:** Piksel gövdesinin uzunluğu tam olarak `n × size × size × 3` olmalı; kalan bayt varsa dosya reddedilmeli.

### 5. [P2] İlan edilen pandas 2.0/2.1 desteği CSV değerlendirme komutuyla uyumsuz

**Yer:** [`requirements.txt:7`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/requirements.txt#L7), [`scripts/eval_app_csv.py:57`](https://github.com/Nisagwn/rppg/blob/8f07ccac2a04f053f626d05238b933838104f361/scripts/eval_app_csv.py#L57).

Bağımlılık `pandas>=2.0`; çağrı ise `.apply(summary, include_groups=False)`. `include_groups`,
[resmî pandas API belgesine göre 2.2.0'da eklendi](https://pandas.pydata.org/pandas-docs/version/2.2/reference/api/pandas.core.groupby.DataFrameGroupBy.apply.html).
2.0/2.1'de bu argüman gruplama seçeneği olarak tanınmaz; kullanıcı fonksiyonuna aktarılır. `summary` bu argümanı kabul etmediği için komut TypeError ile durur.

**Kanıt sınırı:** Yerel ortam pandas 3.0.6; 2.0/2.1 ortamı kurulup çalıştırılmadı. Uyumsuzluk, deklarasyon/çağrı karşılaştırması ve resmî sürüm bilgisiyle saptandı.

**Beklenen:** Ya alt sınır 2.2 yapılmalı ya da gruplama kodu ilan edilen 2.0 sürümüyle uyumlu olmalı.

## İlk dört bulguyu yeniden üretme

Depo kökünde aşağıdaki Python kodu çalıştırılabilir. Yalnız geçici klasör oluşturur; veri seti, model, ağ veya GPU gerektirmez.

```python
import json
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, "scripts")
from import_own import read_ppg, read_rec
from eval_app_csv import read_refs, summary

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)

    p = root / "headerless.csv"
    p.write_text("1700000000000,0\n1700000000017,1\n1700000000034,2\n",
                 encoding="utf-8")
    times, values = read_ppg(p)
    print("1: rows, first_time =", len(times), times[0])

    p = root / "unsorted.csv"
    p.write_text("time,value\n0,0\n2000,100\n1000,10\n3000,20\n",
                 encoding="utf-8")
    times, values = read_ppg(p)
    order = np.argsort(times)
    print("2: actual, sorted =", np.interp(1500, times, values),
          np.interp(1500, times[order], values[order]))

    p = root / "missing.csv"
    p.write_text("zaman,tur,kamera,uygulama_bpm,cihaz_bpm,fark,guvenilir,snr_db,model\n"
                 "now,canli,on,72,74,-2,1,4,tur5\n"
                 "now,canli,on,,74,,1,4,tur5\n", encoding="utf-8")
    result = summary(read_refs(str(p)))
    print("3: n, MAE, p5 =", result["n"], result["MAE"], result.iloc[2])

    header = json.dumps({"size": 72, "n": 2, "t": [0, 1 / 30]}).encode()
    p = root / "extra.rppgrec"
    p.write_bytes(b"RPPGREC1" + struct.pack("<I", len(header)) + header
                  + bytes(2 * 72 * 72 * 3) + b"\xff")
    _, frames = read_rec(p)
    print("4: accepted frames =", len(frames))
```

Gözlenen çıktı:

```text
1: rows, first_time = 2 1700000000017.0
2: actual, sorted = 75.0 55.0
3: n, MAE, p5 = 2.0 2.0 50.0
4: accepted frames = 2
```

## Çalıştırılan kontroller ve sınırlar

- Python 3.12.3, NumPy 2.5.3, pandas 3.0.6; Node.js v22.20.0.
- `CUDA_VISIBLE_DEVICES=-1` ile `.venv/Scripts/python.exe -m pytest -q`: **57 geçti**, 53.63 saniye.
- `node --test mobile/test/dsp.test.mjs mobile/test/dl_pack.test.mjs mobile/test/face_decode.test.mjs mobile/test/model_selection.test.mjs`: **16 geçti**.
- Yukarıdaki küçük örnekler mevcut testlerde kapsanmayan davranışları gösteriyor. Yeni test veya düzeltme eklenmedi.
- GPU, yeni eğitim, gerçek telefon/oksimetre deneyi veya yeni model çıkarımı çalıştırılmadı. Önceki eğitim sonuçları yeniden hesaplanmadı; bulguların bu sonuçları etkilediği gösterilmedi.
