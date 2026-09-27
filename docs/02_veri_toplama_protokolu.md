# Veri Toplama Protokolü

Bu protokol, kendi küçük veri setini **tekrarlanabilir ve etik** biçimde toplamak için hazırlanmıştır.

## 1. Ekipman

| Ekipman | Not |
|---|---|
| Webcam (dizüstü dahili kamera olabilir) | 640×480, 30 fps yeterli |
| Referans cihaz | Parmak tipi pulse oksimetre (~300–600 TL) **veya** nabız ölçen akıllı saat |
| Tripod veya sabit zemin | Kamera kayıt boyunca oynamamalı |
| Sabit ışık kaynağı | Masa lambası; titreşimsiz LED tercih edilir |

> **Kalibrasyon:** Oksimetrenin kendisinin de ±2 BPM civarında hatası vardır. Bu nedenle raporda "referans" denir, "gerçek değer" denmez.

## 2. Kamera Ayarları

`scripts/record_session.py` otomatik pozlamayı ve otomatik beyaz dengesini **kapatmayı dener**. Kameranın bunu desteklediğini `meta.json` içindeki `oto_pozlama` değerinden kontrol edin.

- Windows'ta DirectShow arka ucu kullanılır. Bazı kameralar Windows Kamera uygulamasından manuel pozlamaya alınabilir.
- Kayıt **FFV1 (kayıpsız)** codec'iyle yapılır. JPEG/MJPG sıkıştırması nabız sinyalini zayıflatır; sentetik benchmark'taki "JPEG sıkıştırma" senaryosu bunu gösterir.
- Her kare için monotonik zaman damgası `frames.csv`'ye yazılır. Analizde sabit 30 Hz'e yeniden örneklenir.

## 3. Koşul Matrisi (her katılımcı için)

| # | Koşul kodu | Süre | Talimat |
|---|---|---|---|
| 1 | `gunisigi_sabit` | 60 s | Pencere ışığı, hareketsiz, kameraya bak |
| 2 | `floresan_sabit` | 60 s | Tavan floresanı, hareketsiz |
| 3 | `los_isik` | 60 s | Yalnızca ekran ışığı ve loş oda |
| 4 | `ekran_isigi` | 60 s | Ekranda renkli video oynarken, yüze ekran ışığı vuruyor |
| 5 | `konusma` | 60 s | Kameraya bakarak kendini anlatma, doğal konuşma |
| 6 | `bas_hareketi` | 60 s | Yavaşça sağa-sola ve yukarı-aşağı bakma |
| 7 | `egzersiz_sonrasi` | 90 s | 30 s yerinde koşu ya da 20 çömelmenin hemen ardından (HR yüksek ve değişken) |

**Örnek komut:**
```
python scripts/record_session.py --subject K01 --condition gunisigi_sabit --duration 60
```
Kayıt sırasında **SPACE** tuşuna basıp referans cihazdaki değeri konsola yazın (ör. her 15 s'de bir). Referans değer girilmezse, kayıt sonunda başlangıç ve bitiş değerleri sorulur.

**Akıllı saat kullanılıyorsa:** Saatin uygulamasından HR verisini CSV olarak dışa aktarın. Kayıt başlangıç saatine göre hizalayıp `reference.csv` dosyasına `zaman_s,hr_bpm` biçiminde yazın.

## 4. Katılımcılar ve Çeşitlilik

- Hedef 5–10 gönüllü (ör. sınıf arkadaşları).
- Mümkünse farklı cilt tonları, gözlüklü/gözlüksüz, sakallı/sakalsız katılımcılar alın. Literatürde koyu cilt tonlarında SNR'ın düştüğü bilinmektedir (Nowara vd. 2020); bu fark raporda tartışılmalıdır.
- Her katılımcıya anonim bir kod verilir (K01, K02, ...). Gerçek isim hiçbir dosyada geçmez.

## 5. Etik ve KVKK

Yüz videosu **kişisel veridir** (6698 sayılı KVKK). Bu nedenle:

1. Her katılımcıdan aşağıdaki gibi yazılı onam alın.
2. Videolar yalnızca yerel diskte ve şifreli klasörde tutulur. GitHub'a veya buluta **yüklenmez**.
3. Raporda yüz görüntüsü yalnızca açık izin verenler için kullanılır. Diğerlerinde bulanıklaştırın ya da yalnızca sinyal grafiklerini kullanın.
4. Proje bitiminde ham videolar silinir; yalnızca çıkarılmış RGB izleri (`.npz`) saklanabilir. Bunlar yüzü yeniden oluşturmaz.
5. Ders projesi için genellikle etik kurul gerekmez; ancak danışman hocaya danışın.

### Onam Formu (örnek)

> Fırat Üniversitesi Yazılım Mühendisliği, Sayısal Görüntü İşleme dersi kapsamındaki "Kamerayla Temassız Nabız Ölçümü" projesine gönüllü olarak katılıyorum. Yüzümün yaklaşık 8 dakikalık video kaydının alınacağını, kayıtların yalnızca bu proje kapsamında nabız ölçüm algoritmalarını test etmek için kullanılacağını, üçüncü kişilerle paylaşılmayacağını ve proje bitiminde silineceğini anladım. Katılımdan istediğim zaman ayrılabileceğimi biliyorum.
>
> Raporda/sunumda yüz görüntümün kullanılmasına: ☐ İzin veriyorum ☐ İzin vermiyorum
>
> Katılımcı kodu: ____  Tarih: ____  İmza: ____

## 6. Analiz

```
python scripts/run_video.py --recording data/kayitlar/K01_gunisigi_sabit_20261015_141500
```
Tüm kayıtlar için koşul bazlı tablo üretmek, `scripts/evaluate_ubfc.py` örnek alınarak yazılabilir. Önerilen analizler:

- Koşul × yöntem MAE ısı haritası
- Konuşma ve hareket koşullarında Viterbi+hareket güveni açık/kapalı karşılaştırması
- Ekran ışığı koşulunda ROI ağırlıklarının zaman içindeki değişimi
