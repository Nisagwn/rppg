# Kendi Veri Setimiz — Yol Haritası

Bu belge `02_veri_toplama_protokolu.md`'yi derin öğrenme aşamasına göre günceller. Eski protokol webcam ve elle
okunan nabız değerleri için yazılmıştı. Derin öğrenme ve uygulama doğrulaması için iki şey eksikti:
**sürekli referans dalgası** (parmak PPG'si) ve **telefon kamerası**.

## 1. Neden gerekli?

| İhtiyaç | Şu anki durum | Kendi veriyle |
|---|---|---|
| Uygulamanın gerçek hatası | Chrome'a video verilerek ölçülüyor (MCD, 10 kişi) | Gerçek telefonda, oksimetreye karşı |
| Ticari ürünlerle karşılaştırma | Aynı koşullarda yapılamıyor | Aynı kişi, aynı anda |
| Telefon görüntüsüyle eğitim | Yalnızca MCD'nin tek telefonu (Iriun) | Farklı telefonlar, ön ve arka kamera |
| Cilt tonu çeşitliliği | Test edilmedi | Fitzpatrick ölçeğiyle kayıtlı |
| Makale katkısı | — | Türkiye'den telefonla kaydedilmiş, senkron referanslı ilk rPPG verisi olabilir |

## 2. Ekipman

| Ekipman | Neden | Not |
|---|---|---|
| **Parmak oksimetresi, sürekli dalga çıkışlı** (ör. Contec CMS50E / CMS50D+, USB) | Eğitim için nabız dalgası gerekir, tek bir sayı yetmez. UBFC-rPPG ve PURE'da bu cihaz ailesi kullanılmıştır | **Almadan önce** canlı dalga (60 Hz) aktarımını desteklediğini doğrulayın; bazı modeller yalnızca SpO2/nabız sayısı kaydeder |
| (İsteğe bağlı) **Göğüs bandı** (ör. Polar H10, Bluetooth) | EKG tabanlı nabız: oksimetreden daha güvenilir ikinci referans | Hareketli koşullarda oksimetre de bozulur; ikisi uyuşmayan pencereler çıkarılır |
| Telefon tutucu / tripod | Sabit koşullar için | Elde tutma ayrı bir koşul |
| Masa lambası (titreşimsiz LED) | Tekrarlanabilir ışık | Loş ışık koşulu için kısılabilir |
| 2 telefon (Android + iPhone, mümkünse) | Kamera ve sıkıştırma farkı | Android'de **Open Camera** pozlamayı kilitleyip yüksek bit hızında kayıt yapabilir |
| Dizüstü bilgisayar | Oksimetreyi kaydeder ve senkron için ekranda işaret gösterir | |

## 3. İki kayıt türü

**A. Uygulama doğrulaması (video saklanmaz).** Kişi uygulamayı kendi telefonunda açar ve ölçüm yapar. Uygulama
saniyelik nabzı CSV olarak indirir (bu özellik var), oksimetre aynı anda bilgisayara kaydeder. Yüz videosu
saklanmadığı için KVKK yükü çok azdır. Bu kayıtlar "uygulamanın gerçek hatası" ve ticari karşılaştırma içindir.

**B. Video veri seti (eğitim ve test).** Telefonun kendi kamerasıyla 1080p, 30 fps, en yüksek kalitede kayıt alınır;
oksimetre aynı anda kaydeder. Bu kayıtlar modeli ince ayarlamak ve çevrimdışı test için kullanılır.

## 4. Senkron

- Oksimetre bilgisayarın saatiyle kaydedilir. Kaydın başında ve sonunda bilgisayar ekranı 3 kez beyaz yanıp söner
  ve bip sesi çalar; telefon kamerası ekranı görecek şekilde konur. Videoda yanıp sönmenin olduğu kare, oksimetre
  kaydındaki zamana eşlenir.
- Kalan küçük kayma, MCD ve VIPL için geliştirdiğimiz **model tabanlı hizalamayla** (`scripts/dl_sync_check.py`)
  video başına düzeltilir. Bu yöntem açık veri setlerinde 4–34 karelik kaymaları buldu; kendi verimizde de aynı
  denetim yapılır.
- A türünde telefon ve bilgisayarın saati internetten otomatik ayarlı olmalıdır; 10 saniyelik pencerelerde
  1 saniyenin altındaki fark önemsizdir.

## 5. Koşul matrisi (kişi başına ~25 dakika, kayıtlar 60 s)

| # | Kod | Kamera | Durum | Neden |
|---|---|---|---|---|
| 1 | `on_sabit` | Ön, tutucuda | Hareketsiz, lamba önden | Taban çizgisi |
| 2 | `on_elde` | Ön, elde | Hareketsiz | Uygulamanın asıl kullanımı (el titremesi) |
| 3 | `arka_sabit` | Arka, tutucuda | Hareketsiz | Arka kamera daha kaliteli |
| 4 | `los` | Ön, tutucuda | Yalnızca ekran ışığı | DLCN'de iyi sonuç; gerçek telefonda? |
| 5 | `karsi_isik` | Ön, tutucuda | Pencere arkada | Kullanıcıların sık hatası |
| 6 | `konusma` | Ön, tutucuda | Doğal konuşma | Uygulama içi hata kaynağı |
| 7 | `bas_hareketi` | Ön, elde | Yavaş sağa-sola bakma | Yüz bulucu ve takip |
| 8 | `egzersiz_sonrasi` | Ön, elde | 30 s yerinde koşu sonrası, 90 s | Yüksek ve değişen nabız (testlerde en zor koşul) |

A türü (uygulama) için 1, 2, 4 ve 8 numaralı koşullar yeterlidir (~8 dakika).

## 6. Katılımcılar

- **Hedef 30 kişi, en az 20.** 20 kişi × 8 koşul = 160 dakikalık kayıt; kişi bazlı ayırmayla
  (ör. 15 eğitim / 5 test) ince ayar ve test için yeterli.
- Çeşitlilik: cilt tonu (Fitzpatrick I–VI, kişinin kendi beyanıyla ya da renk kartıyla), yaş grubu, gözlük, sakal.
  Literatürde koyu tonlarda sinyal zayıflıyor (Nowara vd. 2020); her grupta en az 3–4 kişi olmalı.
- Her kişiye anonim kod (K01, K02, …). İsim hiçbir dosyada geçmez.

## 7. Etik ve KVKK — **en uzun süren adım, hemen başlanmalı**

- Makale yayımlamak için çoğu dergi **etik kurul onayı** ister. Fırat Üniversitesi'nin girişimsel olmayan
  araştırmalar etik kuruluna başvuru danışmanla birlikte yapılır; onay birkaç hafta sürebilir. Onay gelmeden
  yalnızca kendi kaydınızla pilot yapılabilir.
- Gerekenler: aydınlatma metni (KVKK), onam formu, protokol özeti (bu belge), veri saklama planı.
- Onam formunda açıkça yazılmalı:
  - Video kaydı alınacağı (B türü).
  - Verinin eğitim için gizli bir bulut deposuna (ör. Hugging Face, gizli) yükleneceği; Kaggle'da eğitim için bu
    gerekli.
  - Saklama süresi.
  - Veri setinin ileride araştırmacılarla paylaşılıp paylaşılmayacağı. Ayrı bir onay kutusu olmalı; paylaşıma izin
    vermeyenler yalnızca kendi testlerimizde kullanılır.
- Yüz görüntüsü raporda yalnızca açık izinle kullanılır.

## 8. Yazılacak araçlar

| Araç | Ne yapar |
|---|---|
| `scripts/oximeter_record.py` | Oksimetreden USB ile 60 Hz dalga + nabız + SpO2 okur, bilgisayar saatiyle kaydeder; senkron için ekranı yakıp söndürür |
| `scripts/import_own.py` | Telefon videosu + oksimetre kaydını senkron işaretinden hizalar, `dl_prepare` biçimine (72×72 kırpıntı `.npy` + etiket `.npz`) çevirir; `kendi/` ve `test_kendi/` |
| `scripts/eval_app_csv.py` | Uygulamanın CSV'sini oksimetre kaydıyla karşılaştırır: MAE, ≤5 BPM %, ortalama yüzde hata (tüketici standardı %10), Bland–Altman |
| Uygulamaya "çalışma modu" | Katılımcı kodu ve koşul seçilir; CSV'ye eklenir (video kaydetmez) |

## 9. Zaman çizelgesi (19 Ekim 2026 → Şubat 2027)

| Hafta | Tarih | İş |
|---|---|---|
| 1 | 19–25 Eki | Danışmanla görüşme; oksimetrenin dalga aktarımını doğrulayıp sipariş; etik kurul ve KVKK belgeleri |
| 2–3 | 26 Eki – 8 Kas | `oximeter_record.py`, `import_own.py`, `eval_app_csv.py`; kendinle pilot kayıt; senkron ve kalite denetimi; protokolü düzelt |
| 4 | 9–15 Kas | Etik kurul başvurusu sonuçlanınca 2–3 kişiyle ikinci pilot |
| 5–9 | 16 Kas – 20 Ara | 20–30 katılımcı (haftada 5–6 kişi, kişi başı ~30 dk); her hafta kayıtlar hazırlanıp kalitesi denetlenir |
| 10 | 21–27 Ara | Kendi test kümesinde mevcut modellerin ve uygulamanın sonuçları (A türü) |
| 11–12 | 28 Ara – 10 Oca | Kendi verinin eğitim kısmıyla ince ayar (Kaggle); kendi testinde ve diğer testlerde karşılaştırma |
| 13–16 | 11 Oca – Şub | Rapor ve makale; cilt tonu ve koşul bazlı analiz, Bland–Altman |

**Kritik yol:** etik kurul onayı ve oksimetrenin dalga aktarımı. İkisi de 1. haftada başlamazsa takvim kayar.

## 10. Riskler

| Risk | Önlem |
|---|---|
| Oksimetre dalga vermiyor | Almadan önce doğrula; olmazsa göğüs bandı (yalnızca nabız, eğitim için yetmez ama test için yeter) |
| Etik onayı gecikir | A türü için danışmanın görüşüne göre ders projesi kapsamında başla; makale için onayı bekle |
| Telefon otomatik pozlama ve sıkıştırma | Open Camera ile pozlama kilidi, yüksek bit hızı; koşulları meta veriye yaz |
| Hareketli koşullarda oksimetre bozulur | Etiket kalite denetimi (`dl_quality.py`) var; bozuk pencereler çıkarılır; göğüs bandıyla çapraz kontrol |
| Katılımcı bulmak | Sınıf ve bölüm; kayıt 30 dakikayı geçmesin |
