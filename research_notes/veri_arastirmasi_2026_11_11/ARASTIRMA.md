# Telefon rPPG modeli için ek veri kaynakları

Kontrol tarihi: 11 Kasım 2026. Kaynaklar: veri sahiplerinin sayfaları, resmî depolar ve makaleler. “Erişim yolu doğrulandı”, başvurunun onaylandığı veya dosyaların tamamının indirildiği anlamına gelmez. Öneri sıralaması bu projenin son kamera testlerine göre yaptığımız değerlendirmedir.

## Mevcut projede zaten bulunanlar

MCD-rPPG, UBFC-rPPG, PURE, UBFC-Phys, mini-MMPD, VIPL-HR, COHFACE ve DLCN için yükleme/eğitim altyapısı var. Önceki araştırma notlarında VitalVideos, MPU-rPPG ve SCAMPS da yer alıyor. Bunları yeni keşif olarak sunmuyoruz. Önceki G koşusunda çoklu veri ve artırmalar da denenmiş; “daha çok veri her durumda iyidir” varsayımı desteklenmiyor. Yeni kaynağın katkısı aynı kontrol koşusuna karşı ölçülmeli.

## Öncelikli adaylar

| Aday | Doğrulanan kapsam | Bu proje açısından kullanım | Erişim / durum |
|---|---|---|---|
| **MHAD** | 40 kişi, 1440 video; evde 6 etkinlik, önden/45°/90°; PPG dahil fizyolojik sinyaller | Hareket ve yan açı çeşitliliği için eğitim adayı. “Telefon kullanma” etkinliği telefon kamerasıyla kayıt demek değildir; kameralar USB'dir | Akademik e-posta ile bireysel başvuru; ticari kullanım yasak. Başvuru yolu doğrulandı, erişim alınmadı |
| **CHILL** | 45 kişi, 180 × 1 dakika; 1080p, 25 fps; aydınlık/karanlık × dinlenme/yüksek nabız | İlk etapta tamamen dışarıda tutulan düşük ışık/yüksek nabız testi | Akademik lisans anlaşması ve başvuru; erişim alınmadı |
| **PhysDrive** | Tam sette 48 kişi, yaklaşık 24 saat; araç içi RGB/NIR, farklı ışık/yol/hareket, BVP/ECG | Tam RGB kaynağı, değişen güneş/ışık ve hareket için aday | Tam ham veri anlaşma ile. Kaggle paketi **yalnız bir kişinin ham RGB/NIR örneğini** içeriyor; bütün kişilerin mmWave verisi RGB eğitim verisi değildir |
| **LADH** | README erişim bölümünde 21 kişi, 240 video, 133.22 GB; 11 kişi 10 gün izlenmiş; bakım hareketleri ve egzersiz sonrası | Günler arası değişim, örtülme ve hareket için ikinci aşama aday | Öğretim üyesinin kurumsal başvurusu ve anlaşma gerekli |
| **iBVP** | 124 × 3 dakika RGB/termal oturum; hareket görevleri; 30 Hz BVP ve sinyal kalite etiketleri; sıkıştırılmış paket yaklaşık 400 GB | RGB kolu + PPG kalite etiketleri değerli; telefonla çekilmiş bir set değil | Akademik danışmanın dolduracağı EULA, yazar onayı gerekli |
| **Tricam-rPPG** | 31 kişi; RGB ve 850/940 nm NIR; 125 Hz parmak PPG; sıcak/soğuk ışık, profil | RGB/ten tonu/aydınlatma için yeni ikincil aday; NIR için telefonumuzda sensör yok | Data Use License ve yazar onayı gerekli |
| **EMPD** | 83 kişi, 193 × 68 s; yüz RGB 640×480/30 Hz; temas PPG 60 Hz | Başvuru beklemeden incelenebilen ek RGB kaynağı. Telefon değil, endüstriyel kamera; hedef çeşitliliğine katkısı ayrıca ölçülmeli | Zenodo API'de açık CC-BY-4.0. Küçük metadata, ilk PPG dosyası ve arşiv başlıkları teknik olarak kontrol edildi |

### Resmî kaynaklar ve başvuru yolları

- **MHAD:** [resmî depo](https://github.com/jdh-algo/MHAD-Dataset), [makale](https://arxiv.org/html/2409.09366v1). `feijintao3@jd.com`, konu `MHAD Dataset Access Request`. Kurumsal e-posta; ad, kurum, akademik görev ve kullanım açıklaması isteniyor. Video ve etiket dosyaları aynı alt klasörde. CSV sütunları/örnekleme ve zaman damgası uyumu veri geldiğinde sınanmalı.
- **CHILL:** [üniversite sayfası](https://www.uni-bielefeld.de/fakultaeten/technische-fakultaet/arbeitsgruppen/human-centered-artificial-intelligence/research/rppg/), [anlaşma](https://www.uni-bielefeld.de/fakultaeten/technische-fakultaet/arbeitsgruppen/human-centered-artificial-intelligence/research/rppg/CHILL-EULA.pdf). Sayfa Bhargav Acharya'yla irtibatı söylüyor; PDF'nin ilk sayfasında imzalı form için `drimalla@techfak.uni-bielefeld.de` yazıyor. Başvuruda bu iki resmî yönerge birlikte dikkate alınmalı.
- **PhysDrive:** [resmî depo](https://github.com/WJULYW/PhysDrive-Dataset), [Kaggle örneği](https://www.kaggle.com/datasets/xiaoyang274/physdrive). Tam veri: `xyang856@connect.hkust-gz.edu.cn`; akademik kullanım, ticari kullanım yasak. Kodun MIT etiketi, veri koşullarını değiştirmiyor. Önceki nottaki “hazır paket yalnız STMap” açıklaması güncel README ile uyuşmuyor: artık bir kişilik ham RGB/NIR örneği de belirtiliyor.
- **LADH:** [resmî depo](https://github.com/McJackTang/FusionVitals), [anlaşma](https://github.com/McJackTang/FusionVitals/blob/main/LADH_Release_Agreement.pdf). `tjk24@mails.tsinghua.edu.cn`, CC `yuntaowang@tsinghua.edu.cn`; konu `LADH Access Request - [kurum]`. Başvuruyu öğretim üyesi göndermeli. README özetinde 11, kurulumunda 21 kişi geçiyor; 11 uzunlamasına alt grup, toplam 21 ifadesiyle birlikte raporlandı. Gerçek dosya manifesti gelince sayılar doğrulanmalı.
- **iBVP:** [resmî depo ve EULA](https://github.com/PhysiologicAILab/iBVP-Dataset). `jitesh.joshi.20@ucl.ac.uk` ve `youngjun.cho@ucl.ac.uk`. Danışman tarafından doldurulan EULA gerekir. Yalnız RGB kısmını talep etmek termal dosya maliyetini azaltabilir; bunun mümkün olduğu henüz doğrulanmadı.
- **Tricam:** [resmî proje](https://tricam-rppg.github.io/), [kod/erişim](https://github.com/Tricam-rPPG/Tri-Cam-rPPG_Codes). `asarkar@vtti.vt.edu` ve `abbott@vt.edu`. RGB, PPG ve ilgili zaman damgaları istenmeli; NIR başarısı RGB telefon başarısı gibi sunulmamalı.
- **EMPD:** [Zenodo ana kayıt](https://zenodo.org/records/18765701), [makale](https://arxiv.org/abs/2603.26699). Dosya bazında lisans/boyut kontrolü `empd_dogrulama.json`, sütun doğrulaması `empd_format.json` içindedir.

## EMPD için teknik doğrulama

Dokuz kaydın Zenodo API dosya boyutları toplandı: **413.69 GB** (ondalık), yaklaşık 385.3 GiB. Önceki nottaki 7.5 TB, indirme boyutu olarak kullanılmamalı; Zenodo'nun “data volume” istatistiği dosya boyutu değildir.

İlk arşivin yalnız 12 TAR başlığı HTTP Range ile okundu. İçerik örüntüsü `csv/<recording>.csv`, `event/<recording>.raw`, `rgb_640_480/<recording>.avi`. Sunucu Range için HTTP 206 döndürdü. Event gövdeleri atlanarak RGB ve PPG'nin seçilerek indirilmesi teknik olarak mümkün; bunun için veri yükleyicisi henüz yazılmadı. Tüm arşivler/oturumlar indirilmedi.

Küçük global metadata 193 kayıt içeriyor: `Filename`, `Label(rest:0,elevate:1)`, `Gender(male:0,female:1)`, `Participants`. İlk PPG CSV'sinde `Count`, `PPG` ve 4080 satır var; 60 Hz / 68 s bilgisiyle tutarlı. Katılımcı kimliği metadata üzerinden kullanılmalı; kayıt zamanını kişi kimliği saymak aynı kişinin eğitim/teste dağılmasına yol açar. İlk dört RGB dosyası yaklaşık 680–726 MB/adet; bütün RGB boyutu henüz taranmadı.

## Hemen önermediklerimiz / bilinen setlerin genişletilmesi

- **LGI-PPGI:** [resmî README](https://github.com/partofthestars/LGI-PPGI-DB) artık depolama/bant genişliği nedeniyle indirme oturumlarının bulunmadığını söylüyor. Eski altı ZIP bağlantısı hâlâ listeleniyor; çalışan erişim doğrulanmadan “hemen indirilebilir” denemez.
- **SUMS:** [resmî depo](https://github.com/thuhci/SUMS). 10 kişi, 80 yüz/parmak videosu, yüksek irtifa/oksijen toparlanması. Başvuruyu öğretim üyesi yapmalı. Telefon/ışık/hareket hedefimiz için MHAD ve CHILL'in gerisinde.
- **Full MMPD:** [resmî depo](https://github.com/THU-CS-PI/MMPD_rPPG_dataset). Telefonda çekilmiş 33 kişi, 11 saat; tam sürüm 320×240/~370 GB, mini 80×60/~48 GB. **Yeni insanlar içeren yeni veri seti değil**, mevcut mini-MMPD'nin daha yüksek çözünürlüklü sürümü. Tam sürüm eğitimine geçersek mini sürümde test için ayrılmış kişilerin bütün sürümleri testte kalmalı. Erişim için öğretim üyesi başvurusu gerekli.

## Somut deney sırası

1. **Erişim başvuruları:** MHAD ve CHILL öncelikli; ardından PhysDrive tam RGB ve LADH. Bu araştırmada e-posta gönderilmedi, anlaşma imzalanmadı.
2. **Kontrollü mevcut-veri deneyi:** `kaggle/rppg_telefon_uyarlama.ipynb` hazır. A: mevcut tur5 ağırlıkları + MCD üç kamera, standart artırma. B: aynı koşu + `--phone-aug`. C: B + `--box-jitter 0.1`. Aynı seed ve manifestle ayrı koşular; varsayılan B/42, henüz çalıştırılmadı. MCD zaten kullanılan veridir; bu aşama yeni veri kazanımı değildir.
3. **Yeni veri ekleme:** Erişimden sonra önce 1–2 oturumda kare/PPG zamanlaması, kanal/polarite, referans kalitesi ve lisansın özel Kaggle işleme/akademik demo koşulları doğrulanır. Ardından MHAD veya bir başka onaylanan set için yükleyici eklenir. Mevcut kodda bu yeni setler destekleniyor varsayılmaz.
4. **Katkıyı ayırma:** Aynı model ve artırmalarla önce mevcut veri, sonra mevcut + yeni veri. Her varyantta 42/43/44 tohumları; veri ve kişi ayrımı sabit. Birden çok yeni seti aynı anda ekleyip hangisinin yararlı olduğunu belirsiz bırakmayalım.
5. **Dış test:** CHILL ilk etapta eğitim dışı tutulur. MHAD/LADH'de aynı kişinin farklı günleri ve kameraları aynı bölmede olmalı. Son telefon/oksimetre kayıtları geliştirme verisinden ayrı tutulur. Önceden defalarca incelenen MCD/UBFC testleri yeni ve bağımsız son test diye sunulmaz.

## Kaggle uyarlama defteri

<https://github.com/Nisagwn/rppg/blob/main/kaggle/rppg_telefon_uyarlama.ipynb>

İlk 100 test-dışı MCD kişisi, üç kamera, ilk 30 s; 20 epoch × 300 adım, başlangıç tur5, LR 5e-5. Bunlar başlangıç deney ayarlarıdır, optimal oldukları gösterilmedi. A/B her koşuda aynı veri listesiyle karşılaştırılmalı. Test: MCD'nin önceden ayrılmış 10 kişisinin 60 kaydı; yüz filtresi geçen gerçek sayılar raporlanır. Her iki model hop=160 ve hop=80 ile, argmax/Viterbi altında aynı dosyalarda ölçülür. Sonuç yedekleri varyant/seed/kişi sayısıyla ayrılır. Otomatik uygulama modeli değişikliği yok.

Bu bilgisayarda Kaggle API erişimi bulunmadığından yeni eğitim başlatılmadı. Erişim gerektiren veri setlerinin ham dosyaları indirilmedi. EMPD'de yalnız küçük metadata/PPG örneği ve TAR başlıkları incelendi; bu aşama eğitim tamamlanmış gibi raporlanmaz.
