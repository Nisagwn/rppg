# Açık erişimli akademik rPPG (yüz videosu + temas PPG) veri setleri — Ekim 2026

Etiketler: **doğrulandı** = bu oturumda resmi sayfa/kayıt (GitHub README, Zenodo/Mendeley kaydı, lab sayfası) açılıp okundu. **iddia** = yalnızca ikincil kaynak (arama özeti, derleme sayfası, makale) üzerinden; resmi sayfa açılamadı ya da indirme denenmedi. Hiçbir indirme bağlantısı gerçekten indirilerek test edilmedi; "açık" ifadesi sayfadaki erişim koşuluna dayanır.
Hariç tutulanlar (MCD-rPPG, UBFC-rPPG, PURE, UBFC-Phys, MMPD, VIPL-HR, COHFACE, VitalVideos, MPU-rPPG, SCAMPS) yalnızca yeni ayna/sürüm bulunduğunda anılmıştır.

## S1 — 2016–2026 arası hangi rPPG veri setleri gerçekten imzasız/formsuz indirilebiliyor?

### Takeaway
İmzasız indirilebilen, ham yüz videosu + senkron PPG dalga formu içeren yeni aday sayısı az: en değerlileri **EMPD (Zenodo, CC-BY-4.0, 83 kişi, PPG 60 Hz)**, **MR-NIRP (Rice, Google Drive, NIR+RGB, PPG 60 Hz)**, **LGI-PPGI-DB (CC-BY-4.0, ama 25 kişiden yalnız 6'sı indirilebilir)** ve **Rice CameraHRV (Box linki)**. Diğer "açık" kayıtlar ya ön-işlenmiş kırpıntı (rPPG-10 64×64, PhysDrive Kaggle) ya HR-only ya da çelişkili erişim etiketine sahip (MPSC-rPPG).

### Cited Findings

**A. Formsuz indirilebilir — ham video + PPG dalga formu (yüksek değer)**

| Veri seti | Kişi / video | Kamera, çözünürlük, fps | Yer gerçeği | Koşullar | Lisans / erişim | Boyut | Durum |
|---|---|---|---|---|---|---|---|
| **EMPD** (Event-based Multimodal Physiological Dataset, arXiv 2603.26699, Mart 2026) | 83 kişi, 193 kayıt × 68 s | Yüz: FLIR BFS-U3-31S4C-C endüstriyel RGB, orijinal 2048×1536 @30 fps, **yayında 640×480'e küçültülmüş + sıkıştırılmış**; ayrıca bilekte Prophesee EVK4 event kamera (1280×720, 660 nm lazer) | CONTEC CMS50E parmak PPG **dalga formu + HR, 60 Hz** | Dinlenme ve egzersiz sonrası; HR 40–110 BPM | **CC-BY-4.0, açık** (Zenodo); concept DOI 10.5281/zenodo.18765701 | **~7.5 TB, 9 parça** (Part 4 = 44.5 GB) — event verisi baskın | doğrulandı — [Zenodo Part 4](https://zenodo.org/records/18794932); [arXiv](https://arxiv.org/abs/2603.26699) |
| **MR-NIRP** (MERL-Rice NIR Pulse; Indoor + Driving/Car) | 18 kişi (16E/2K, 25–60 yaş); 19 sürüş + 18 sabit kayıt; garaj 2 dk, sürüş 2–5 dk | NIR Point Grey GS3-U3-41C6NIR-C (940 nm bant geçiren) + RGB FLIR GS3-PGE23S6C-C; 640×640 @30 Hz | CMS 50D+ parmak PPG, 60 Hz | Araç içi sürüş (hareket, güneş ışığı), garaj/iç mekan | Rice sayfasında **doğrudan Google Drive klasörleri** (form yok); eski FTP ftp://ftp.merl.com/pub/tmarks/MR_NIRP_dataset/ | Belirtilmemiş | Erişim doğrulandı — [Rice databases](https://computationalimaging.rice.edu/databases/) (Driving: drive.google.com/drive/folders/1U3fzIOESmaBAyikGF0cKI2wW3YK8JqCK, Indoor: drive.google.com/drive/folders/1huO4AZ6Dbr24gwHFgYvpHPbYUSNBWjGC); teknik detaylar iddia — [MERL TR2018-067](https://www.merl.com/publications/docs/TR2018-067.pdf), [Camera Vitals](https://cameravitals.github.io/datasets.html) |
| **LGI-PPGI-DB** (CanControls / Pilz et al. 2018) | 25 kişi (20E/5K, 25–42 yaş, **ağırlıkla Kafkas**), 100 kayıt, >3 saat | Logitech C270 webcam, **sıkıştırmasız AVI**, 25 fps, otomatik pozlama | CMS50E parmak PPG (60 Hz), seri port ile senkron | 4 oturum: dinlenme, baş/yüz hareketi, **bisiklet egzersizi (5 dk)**, **kentte konuşma (doğal ışık değişimi)** | **CC-BY-4.0**, doğrudan link — ama **yalnız 6/25 kişi indirilebilir**, diğerleri "t.b.c."; tam erişim için info@cancontrols.com | Dosya başına 4.21–7.57 GB | doğrulandı — [GitHub](https://github.com/partofthestars/LGI-PPGI-DB) |
| **Rice CameraHRV** (Pai et al., SPIE BIOS 2018) | 12 kişi (8E/4K) — Rice CI sayfası **14 kişi** diyor (çelişki) | Point Grey Blackfly BFLY-U3-23S6C (Sony IMX249), 1920×1200; fps sayfada yok, Camera Vitals 30 Hz diyor | CMS 50D+ FDA onaylı pulse oksimetre (örnekleme belirtilmemiş) | 5×2 dk: sabit, web okuma, video izleme, konuşma, derin nefes (HRV odaklı) | **Box paylaşım linki, form yok**; lisans belirtilmemiş, 2018 SPIE makalesi + tez atfı isteniyor | Belirtilmemiş | doğrulandı — [sh.rice.edu/camerahrv](https://sh.rice.edu/camerahrv/), [Rice CI](https://computationalimaging.rice.edu/cameraHRV) (link: rice.box.com/s/noy6vn7k5g5bfvl9o6ekcjmgc9ng4yel) |

**B. Formsuz ama sınırlı değer (ön-işlenmiş, HR/ECG-only veya belirsiz)**

| Veri seti | Özet | Erişim | Durum |
|---|---|---|---|
| **rPPG-10** (Data in Brief 2025, "10-minute video dataset in uncontrolled lighting") | 26 Portekizli üniversite öğrencisi (12E/14K, ort. 22.5 yaş), 1 kişi artefakt nedeniyle dışlanmış; her kişi **10 dk**; **yalnız 3 ROI kırpıntısı (alın, sağ/sol yanak) 64×64 AVI** — tam yüz yok; düşük maliyetli RGB webcam, doğal gün ışığı / kontrolsüz aydınlatma; yer gerçeği **ECG** (NumPy), videoyla **elle senkronlanmış**; meta veri: sıcaklık, nem, aydınlık, makyaj/güneş kremi | **Mendeley Data, CC BY-NC-SA 4.0, açık**, DOI 10.17632/bx8982xgwt.1; kod github.com/GRodrigues4/rPPG-10 | doğrulandı — [Mendeley](https://data.mendeley.com/datasets/bx8982xgwt/1), [PMC makale](https://pmc.ncbi.nlm.nih.gov/articles/PMC12311941/) |
| **PhysDrive** (arXiv 2507.19172, 2025) | 48 sürücü, ~24 saat (1.5 M kare); RGB + NIR + mmWave radar; ECG, BVP, solunum, HR, RR, SpO2; 3 araç tipi, 4 aydınlatma, 3 yol durumu, sürücü hareketi | **Ön-işlenmiş veri Kaggle'da anlaşmasız**; **ham veri** veri paylaşım anlaşması (xyang856@connect.hkust-gz.edu.cn); MIT lisansı, yalnız akademik | doğrulandı — [GitHub](https://github.com/WJULYW/PhysDrive-Dataset) (Kaggle dosyasının içeriği — ham kare mi, STMap mi — README'de "spatial-temporal maps and preprocessed labels" deniyor; ham video değil) |
| **"rPPG" (OSF fdrbh)** | 8 kişi (7E/1K), 3 kamera (Logitech C920 1920×1080, MS VX800 640×480, Lenovo laptop 640×480), 15 Hz; yer gerçeği yalnız **nabız hızı** (Choicemmed MD300C318) | OSF linki | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html); OSF sayfası WebFetch ile içerik vermedi |
| **DCC (Dual Camera Collector) / DCC-SFEDU** | Android telefonun ön kamerası yüzü, arka kamerası parmak (kontakt PPG) kaydı; vatandaş-bilim, alt veri setleri kayıt defteri OSF'de | OSF osf.io/urw96 (içerik doğrulanamadı) | iddia — yalnız arama özeti; [OSF](https://osf.io/urw96/) |
| **MPSC-rPPG** (IEEE DataPort) | 7 kişi, 1–3 deneme, yüz videosu + eşzamanlı BVP; ~4.5 GB | **Çelişki**: anahtar kelime listesinde "Open Access" etiketi, belge sayfasında "IEEE DataPort Subscription gerekli" | doğrulandı (çelişki dahil) — [belge](https://ieee-dataport.org/documents/mpsc-rppg-dataset); [liste](https://ieee-dataport.org/keywords/remote-photoplethysmography-rppg) |
| **DDMP-FV** (IEEE DataPort) | Temassız fizyolojik izleme yüz videosu seti; ayrıntı bulunamadı | Listede "Open Access" | iddia — [IEEE DataPort liste](https://ieee-dataport.org/keywords/remote-photoplethysmography-rppg) |
| **Simulated_Multispectral_rPPG** (IEEE DataPort) | UBFC-rPPG'nin 31 bantlı (400–700 nm) **sentetik** multispektral türevi, 42 kişi, HR yer gerçeği | "Open Access" | iddia — aynı liste; gerçek yeni veri değil |

**C. Hariç tutulan setlerin yeni aynaları**
- MCD-rPPG'nin Hugging Face'te ek aynaları var: kyegorov/mcd_rppg (orijinal), luoyongkai/mcd_rppg, dypknu/mcd_rppg — [HF arama](https://huggingface.co/datasets/kyegorov/mcd_rppg). **Bgeorge/RPPG** ham video değil, MediaPipe ile 8 ROI'ye ayrılmış ön-işlenmiş türev + PPG, CC-BY-NC-SA-2.0 olarak etiketlenmiş (orijinal CC-BY-4.0), ~1.15 TB, kapısız — doğrulandı [HF](https://huggingface.co/datasets/Bgeorge/RPPG).
- COHFACE'in Zenodo kaydı (4081054) **açık değil**: dosyalar kısıtlı, kalıcı kadrolu kişinin onayı + EULA, 257 GB — doğrulandı [Zenodo](https://zenodo.org/records/4081054).
- VitalVideos HF sayfaları (Worldwide/Europe-1/Africa-1; Africa-1 = 1,551 Sahra-altı Afrika katılımcısı) talep/lisans ile — iddia [HF](https://huggingface.co/datasets/pjtoye/VitalVideos-Africa-1).
- MPU-rPPG figshare DOI 10.6084/m9.figshare.29377835 (zaten biliniyor) — [Sci Data 2026](https://www.nature.com/articles/s41597-026-07310-3).

### Inferences
- Projeye (FactorizePhys ince ayar, PPG dalga formu gerektiren) doğrudan eklenebilecek en iyi yeni kaynak **EMPD yüz RGB videolarıdır**: 83 kişi, CMS50E 60 Hz (UBFC/PURE ile aynı cihaz ailesi → polarite/gecikme profili benzer olabilir; MCD'deki ters polarite sorununa karşı yine de kontrol edilmeli). Ancak 7.5 TB'ın çoğu event verisi olabilir; yalnız RGB dosyalarını seçerek indirmek için Part 1'deki metadata dosyası incelenmeli. Video 640×480'e yeniden sıkıştırılmış olduğundan sıkıştırma artefaktı bekleyin.
- **MR-NIRP** RGB kanalı + sürüş hareketi, telefon/USB alan kaymasına karşı zorlu bir test seti olarak kullanılabilir; ancak 18 kişi, %89 erkek.
- **LGI-PPGI** sıkıştırmasız ve egzersiz/dış mekan içerdiği için değerli ama yalnız 6 kişi açık — eğitimden çok çapraz-veri testi için uygun.
- rPPG-10 tam yüz değil 64×64 ROI verdiği için yüz-kırpımlı model girişiyle (FactorizePhys) uyumsuz; ECG→PPG dalga formu yerine yalnız HR denetimi sağlar.
- Açık setlerin hiçbirinde koyu ten tonu dengesi belgelenmemiş; LGI "predominantly Caucasian", rPPG-10 Portekizli öğrenciler.

### Gaps
- EMPD: kişi demografisi/ten tonu, RGB dosyalarının toplam boyutu, video codec'i ve RGB–PPG senkron doğruluğu bu oturumda okunmadı (Part 1 metadata ve arXiv tam metni gerekli). Ayrıca Zenodo'da aynı veri için "EPMD: A Multimodal Event-RGB Dataset…" başlıklı ikinci bir seri (record 18755421) görünüyor — isim/sürüm ilişkisi belirsiz ([Zenodo EPMD Part 1](https://zenodo.org/records/18755421)).
- MR-NIRP Google Drive klasörlerinin hâlâ erişilebilir ve tam olduğu, LGI-PPGI CanControls linklerinin çalıştığı, CameraHRV Box linkinin aktif olduğu indirilerek test edilmedi.
- MR-NIRP ve CameraHRV için lisans metni bulunamadı.
- DCC-SFEDU, "CAMPS", "VIPL-V2", "ReViSe", "UBFC-NIR", "Face2PPG" (bu bir veri seti değil, bir yöntem/pipeline; [arXiv](https://arxiv.org/pdf/2202.04101)), "MMRPhys" (model adı) için açık indirme kaydı bulunamadı.

## S2 — Talep/anlaşma gerektiren önemli veri setleri (açıkça işaretli) ve teknik özellikleri

### Takeaway
2023–2026 setlerinin çoğu (iBVP, SUMS, LADH, M3PD, RLAP, BH-rPPG, BUAA-MIHR, UCLA-rPPG, ECG-Fitness, DDPM, CHILL) EULA/DUA ister; Tsinghua (SUMS/LADH/M3PD), Notre Dame (DDPM) ve iBVP **öğrencinin kendi imzasını kabul etmiyor** — danışman/fakülte veya kurumun hukuk birimi imzalamalı. BH-rPPG/BUAA-MIHR yalnız kurumsal e-posta ister (Gmail/163 kabul edilmez).

### Cited Findings

| Veri seti | Kişi / içerik | Kamera, çözünürlük, fps | Yer gerçeği | Koşullar | Erişim (öğrenci?) | Boyut | Kaynak / durum |
|---|---|---|---|---|---|---|---|
| **iBVP** (2024) | 33 kişi (7'si kısıtlı onay), 124 oturum, ~372 dk RGB-termal | Logitech BRIO RGB 640×480 + FLIR A65SC termal 640×512, 30 fps | **Kulak PPG**, 30 Hz'e indirgenmiş, manuel+otomatik sinyal kalite etiketleri | Yavaş nefes, kolay/zor matematik, baş hareketi | EULA; **"academic supervisors" doldurmalı** | ~400 GB | doğrulandı [GitHub](https://github.com/PhysiologicAILab/iBVP-Dataset) |
| **SUMS** (Summit Vitals) | 10 kişi, 80 video (Qinghai platosu, yüksek irtifa) | 2× Logitech C922 (yüz + parmak), 1280×720 @60 fps | PPG **20 Hz** (CMS50E+), solunum 50 Hz, SpO2 | Dinlenme, egzersiz sonrası, oksijen inhalasyonu | Release agreement; **fakülte** kurumsal e-postadan | Belirtilmemiş | doğrulandı [GitHub](https://github.com/thuhci/SUMS/) |
| **LADH** | 21 kişi (10 uzun dönem), 240 video | RGB + IR yüz, 640×480 @30 fps | PPG & SpO2 20 Hz, solunum 50 Hz | Oturma/ayakta dinlenme, diş fırçalama/saç tarama, egzersiz sonrası | Fakülte imzalı anlaşma | 133.22 GB | doğrulandı [GitHub](https://github.com/McJackTang/FusionVitals/) |
| **M3PD** (arXiv 2511.02349) | 13 sağlıklı (lab, ~15 dk) + **47 kardiyovasküler hasta** (klinik, ~30 s) | Telefon ön (yüz) + arka (parmak) kamera eşzamanlı; OPPO A52 / Xiaomi 14; **yayın 128×128 @30 fps .pth tensör** | BVP, HR, RR, SpO2, BP | Lab + klinik | Fakülte imzalı anlaşma (README'de konu satırı yanlışlıkla "LADH Access Request") | Belirtilmemiş | doğrulandı [GitHub F3Mamba](https://github.com/Health-HCI-Group/F3Mamba); [arXiv](https://arxiv.org/abs/2511.02349) |
| **RLAP** | 58 öğrenci, 13 görev (uzaktan öğrenme, oyun, okuma, duygu) | Logitech C930c | CMS50E BVP | Uzaktan öğrenme | İmzalı DUA e-postası → 14 gün geçerli imzalı link | ~642 GB ISO | doğrulandı [GitHub](https://github.com/KegangWangCCNU/RLAP-dataset) |
| **BH-rPPG** (Beihang) | 12 kişi (11E/1K), 36 video × 900 kare, sıkıştırmasız | Logitech C310, ~20 fps (düşük ışıkta kararsız) | CMS50E PPG dalga formu **61 Hz** | Düşük/orta/yüksek aydınlatma | Kurumsal e-posta ile talep (yangze@buaa.edu.cn) | — | doğrulandı [GitHub](https://github.com/yangze68/BH-rPPG-dataset) |
| **BUAA-MIHR** (FG 2020) | 15 kişi, 165 video × 60 s | RGB 30 fps | Parmak PPG 60 Hz | **11 aydınlık seviyesi, 1–100 lux** | Kurumsal e-posta (xilin1991@buaa.edu.cn); Baidu/OneDrive | — | iddia (arama özeti) — [GitHub](https://github.com/xilin-x/Large-scale-Multi-illumination-HR-Database) |
| **UCLA-rPPG** | 104 kaydedilen, 102 kullanılabilir; **geniş ten tonu/etnisite çeşitliliği** | — | — | — | IRB nedeniyle Data Request Form (zhenwang@ucla.edu) | — | iddia — [UCLA VMG](https://visual.ee.ucla.edu/rppg_avatars.htm) |
| **ECG-Fitness** (BMVC 2018) | 17 kişi (14E/3K, 20–53 yaş), 207 × 1 dk | 2× Logitech C920, 1920×1080 @30 fps, sıkıştırmasız YUV | **ECG** (Viatom CheckMe Pro), HR 56–159 (ort. 109) | Fitness aletleri, 3 aydınlatma (doğal, halojen, LED), hareket bulanıklığı | Basılı form imzalanıp e-posta (spetlrad@fel.cvut.cz) | ~200 GB 7z | doğrulandı [CTU](https://cmp.felk.cvut.cz/~spetlrad/ecg-fitness/) |
| **PFF** (Pulse From Face, 2017) | 13 kişi, 3 dk klipler | 1280×720 @50 fps | Yalnız **ortalama HR** (Mio Alpha II) | — | Üniversite e-postası + imzalı form → şifre | — | doğrulandı [GitHub](https://github.com/AvLab-CV/Pulse-From-Face-Database) |
| **TokyoTech Remote PPG** (Maki et al., EMBC 2019) | 9 kişi × 9 × 20 s | — | Kontakt PPG (IBI değerlendirmesi) | — | İmzalı EULA → e-posta linki; ham PNG (173 GB) ayrıca talep | — | iddia — [Okutomi lab](http://www.ok.sc.e.titech.ac.jp/res/VitalSensing/remoteIBI/Dataset.html) |
| **DDPM** + **Remote Pulse Detection '21** (Notre Dame) | DDPM: 70 kişi ~13 saat; RPD'21: 86 kişi × ~10 dk | 1920×1080 @**90 fps** RGB (+NIR, LWIR DDPM'de), kayıpsız sıkıştırma | Nabız dalga formu, HR, SpO2 | Yalan-tespiti mülakatı, serbest hareket | Lisans **kurumun yetkili imzacısı** tarafından; **öğrenci/postdoc imzalayamaz** | DDPM ~12 TB; RPD'21 ~7 TB | doğrulandı [CVRL](https://cvrl.nd.edu/projects/data/) |
| **MSPM** (Notre Dame, arXiv 2402.02224) | 103 kişi (87 PTT alt kümesi), 18–58 yaş | DFK 33UX290 RGB 1920×1080 @90 (üst) / 30 fps (ön), NIR 30 fps, iPhone 13 Pro Max 640×480 @30 | 10 vücut noktasında MAX30101 PPG **400 Hz**, CMS50EA 60 Hz, Omron BP | El kaldırma, yönlendirilmiş nefes, nefes tutma, oyun, film, renk-darbeli saldırı | **Makalede erişim beyanı yok** (muhtemelen CVRL lisansı — doğrulanmadı) | — | doğrulandı (özellikler) [arXiv html](https://arxiv.org/html/2402.02224) |
| **CHILL** (Bielefeld; npj Digit Med 2025) | Makale: 45 kişi, 4 senaryo (düşük/yüksek HR × aydınlık/karanlık), 1920×1080 @25 fps; **Zenodo kaydı: 23 kişi**, 36×36 ön-işlenmiş .npy, **yalnız HR** | — | HR-only | Düşük ışık + yüksek HR (54–141) | Zenodo **kısıtlı**, akademik EULA (bhargav.acharya@uni-bielefeld.de); CC BY-NC-ND 4.0 (makale) | 10.6 GB | doğrulandı (çelişki dahil) — [Zenodo](https://zenodo.org/records/14637544); [arXiv](https://arxiv.org/html/2503.11697v1); [npj](https://www.nature.com/articles/s41746-025-02192-y) |
| **CAST-Phys** (2025) | 60 kişi, 1,080 video, 18 duygu uyaranı | Yüksek çözünürlüklü **sıkıştırmasız** yüz videosu | PPG, EDA, solunum | Duygu uyarımı | IEEE DataPort'ta "upon request" (listede Open Access etiketi — çelişkili) | — | iddia — [IEEE DataPort](https://ieee-dataport.org/documents/cast-phys), [arXiv](https://arxiv.org/pdf/2507.06080) |
| **rPPG-26** (Navdha Bhardwaj) | Kuzey Hindistanlı katılımcılar; **video yok**, yalnız ROI ortalama RGB zaman serisi + RR aralıkları (emWave Pro); 1080p @30 | — | RR aralığı | — | İmzalı form e-postası | — | doğrulandı [GitHub](https://github.com/Navdhabhardwaj/rPPGdataset) |
| **DEAP** (2012, kapsam dışı yıl ama sık kullanılıyor) | 32 kişi; **yüz videosu yalnız ilk 22 kişi**; 861 × 1 dk deneme | — | Kontakt PPG (pletismograf) + GSR, EEG | Müzik videosu izleme | EULA (QMUL sayfası sertifika hatası verdi) | — | iddia — [DEAP readme](https://www.eecs.qmul.ac.uk/mmv/datasets/deap/readme.html), [arXiv 1710.08369](https://arxiv.org/pdf/1710.08369) |
| **MAHNOB-HCI** | 27 kişi; 780×580 @61 fps | — | **ECG** (PPG yok) | Duygu | mahnob-db.eu (bu oturumda 404 döndü) | — | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html) |
| **BP4D+ / MMSE-HR** (Binghamton) | BP4D+: 140 kişi, 18–66 yaş, 1040×1392 @24 Hz; MMSE-HR: 40 kişi, 102 video | — | Parmak manşonu kan basıncı dalga formu | Duygu uyarımı | Binghamton lisans sayfası (koşullar okunmadı) | — | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html), [Binghamton](http://www.cs.binghamton.edu/~lijun/Research/3DFE/3DFE_Analysis.html) |
| **OBF** (Oulu) | Sağlıklı + atriyal fibrilasyon hastaları, RGB + NIR | — | — | — | "Availability unclear" | — | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html) |
| **CMU rPPG (rppg_biases)** | 140 kişi (44 Hindistan, 96 Sierra Leone) — koyu ten | Yalnız küçük ROI kırpıntıları (alın 60×30, yanak 25×25) @15 Hz | Belirtilmemiş | — | GitHub (erişim koşulu okunmadı) | — | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html); repo github.com/AiPEX-Lab/rppg_biases |
| **VicarPPG / VicarPPG-2** | 10 kişi (20–35), 720×1280 @30 | — | CMS50 PPG | VicarPPG-2: HR + kısa dönem HRV | vicarvision.nl sayfası 403 verdi | — | iddia — [Camera Vitals](https://cameravitals.github.io/datasets.html), [arXiv 2012.15846](https://arxiv.org/pdf/2012.15846) |
| **MPSC-rPPG** | yukarıda (S1-B) | | | | DataPort aboneliği | | |

### Inferences
- Öğrenci olarak doğrudan talep edilebilecek olanlar: RLAP (DUA'da imzacı kısıtı README'de belirtilmiyor), BH-rPPG ve BUAA-MIHR (kurumsal e-posta yeterli görünüyor), ECG-Fitness ve PFF (formda imzacı kısıtı sayfada belirtilmiyor). iBVP, SUMS, LADH, M3PD için danışman; DDPM/RPD'21 için üniversitenin hukuk/sözleşme birimi gerekir.
- PPG dalga formu + zor koşul açısından en değerliler: iBVP (kalite etiketli PPG), RLAP (58 kişi, iyi senkron iddiası), MSPM (400 Hz çok noktalı PPG, telefon kamerası dahil), DDPM/RPD'21 (90 fps, 86 kişi).
- Telefon alan kayması (projenin "telefon/USB testi" hedefi) için yeni adaylar: M3PD (ama 128×128 ön-işlenmiş), MSPM (iPhone 13 kanalı).
- Ten tonu çeşitliliği için: UCLA-rPPG, CMU rppg_biases (ROI-only), VitalVideos-Africa (hariç listede).

### Gaps
- UCLA-rPPG kamera/fps/yer gerçeği, BP4D+/MMSE-HR lisans ücreti, DEAP ve MAHNOB'un güncel erişim süreci, VicarPPG-2 erişimi bu oturumda resmi sayfadan doğrulanamadı.
- RLAP fps/çözünürlük ve PPG örnekleme hızı README'de yok.
- MSPM'nin dağıtılıp dağıtılmadığı belirsiz.

## S3 — Erişim bilgisi içeren derlemeler / kataloglar

### Takeaway
Erişim bilgisini satır bazında veren en kullanışlı kaynaklar: rPPG-Toolbox README (desteklenen setler + linkler), Camera Vitals veri seti sayfası (14 set, linkli), IEEE DataPort "remote photoplethysmography" anahtar sayfası (açık/abonelik etiketi). 2025–2026 derlemeleri veri seti tablosu içeriyor ancak bu oturumda tam metinleri açılamadı.

### Cited Findings
- rPPG-Toolbox şu an MMPD, SCAMPS, UBFC-rPPG, PURE, BP4D+, UBFC-Phys, iBVP, **PhysDrive**, **SUMS**, **LADH** destekliyor; her biri için resmi link veriyor — [rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox).
- Camera Vitals: MAHNOB-HCI, BP4D+, VIPL-HR, COHFACE, UBFC-rPPG, UBFC-Phys, Rice CameraHRV, MR-NIRP, PURE, rPPG (OSF), OBF, PFF, CMU PPG, VicarPPG — kişi, kamera, fps, yer gerçeği ve erişim linkiyle — [Camera Vitals](https://cameravitals.github.io/datasets.html).
- IEEE DataPort anahtar kelime sayfası: Simulated_Multispectral_rPPG, CAST-Phys, DDMP-FV, MPSC-rPPG (hepsi "Open Access" etiketli; MPSC belge sayfasıyla çelişiyor) — [IEEE DataPort](https://ieee-dataport.org/keywords/remote-photoplethysmography-rppg).
- "Demographic bias in public remote photoplethysmography datasets" (npj Digital Medicine 2025) kamuya açık rPPG setlerinin demografik tablosunu sunuyor; verisi Zenodo'da — [npj](https://www.nature.com/articles/s41746-025-01973-9) (tam metin bu oturumda yönlendirme nedeniyle açılamadı).
- Diğer 2025–2026 derlemeler: "A comprehensive review of heart rate measurement using rPPG and deep learning" — [PMC12181896](https://pmc.ncbi.nlm.nih.gov/articles/PMC12181896/); "Advancements in Remote Photoplethysmography" (Electronics 2025) — [MDPI](https://www.mdpi.com/2079-9292/14/5/1015); "Roadmap of rPPG from heart rate measurement toward clinical translation" (npj Digit Med 2026) — [npj](https://www.nature.com/articles/s41746-026-02715-1).
- Notre Dame CVRL veri sayfası DDPM ve Remote Pulse Detection '21'i lisans süreciyle listeliyor — [CVRL](https://cvrl.nd.edu/projects/data/). Rice Computational Imaging veri sayfası MR-NIRP ve CameraHRV'yi doğrudan linklerle listeliyor — [Rice](https://computationalimaging.rice.edu/databases/).

### Inferences
- Yeni (2025–2026) açık setleri yakalamanın en verimli yolu Zenodo/arXiv'de "event camera rPPG", "Data in Brief rPPG" gibi dar sorgular ve rPPG-Toolbox'a eklenen yeni loader'ları takip etmek; EMPD ve rPPG-10 bu yolla bulundu.

### Gaps
- npj 2025 demografik yanlılık tablosu ve 2025 PMC derlemesinin veri seti tablosu okunamadı; bu tablolardaki ek adaylar (ör. ten tonu dağılımları) doğrulanmadı.
- Semantic Scholar/Google Scholar sistematik taraması yapılmadı; Çin kaynaklı (Baidu-hosted) setler ve 2026'nın ikinci yarısındaki Scientific Data yayınları eksik kalmış olabilir.
