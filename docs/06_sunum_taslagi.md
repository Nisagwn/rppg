# Sunum Taslağı (15 dk + canlı demo)

Her slayt için başlık, içerik ve konuşma notu verilmiştir. Şekiller `results/` ve `docs/` klasörlerindedir.

---

### 1. Başlık
**Kamerayla Temassız Nabız Ölçümü** — Klasik görüntü işleme ile
Hayrunnisa Güven · Sayısal Görüntü İşleme
> *Not:* Sunuma canlı demo ile başla. Kamera açık, ekranda kendi nabzın görünsün. "Şu an nabzımı hiçbir şey takmadan ölçüyoruz."

### 2. Problem
- Kalp her attığında yüzün rengi değişir, ama piksel başına **yalnızca ~0.3 gri seviye**.
- Kamera gürültüsü ~2–5, ışık değişimleri ~10–50 gri seviye.
- Soru: bu küçük sinyali nasıl çıkarırız?
> *Görsel:* EVM videosundan bir kare (büyütülmüş yüz kırmızı-yeşil nabız atıyor).

### 3. Ders konuları nerede?
Tablo: Haar, NCC, YCrCb, morfoloji, uzamsal ortalama, renk projeksiyonu, FFT, Butterworth, piramit, optik akış.
> *Not:* "Derin öğrenme yok; her adım derste gördüğümüz bir teknik."

### 4. Sistem akışı
`docs/sistem_akisi.png`. Turuncu kutular özgün katkılar.

### 5. Yüz ve cilt
Haar + NCC takip, ROI'ler, YCrCb maske + açma/kapama.
> *Görsel:* canlı demoda `m` tuşuyla maske görünümü.

### 6. Renk uzayı hilesi: POS
- Işık değişimi: tüm kanallar aynı oranda → [1,1,1] yönü
- Nabız: yeşilde güçlü → [0.33, 0.77, 0.53]
- POS düzlemi [1,1,1]'e dik, dolayısıyla ışık değişimi silinir.
> *Görsel:* A ısı haritası (GREEN kırmızı, POS mavi).

### 7. Frekans domeni
Detrend → bant geçiren → spektrum → tepe.
> *Görsel:* `E_ornek_*.png` spektrogram paneli.

### 8. Katkı 1: SNR ağırlıklı füzyon
Alın saçla kapalı, sağ yanağa ekran ışığı vuruyor; sistem otomatik olarak sol yanağa güveniyor.
> *Görsel:* `F_roi_agirlik_hard_s0.png` ve canlı demodaki ROI ağırlık çubukları.

### 9. Katkı 2: Viterbi takibi
Argmax tek pencerede 150 BPM'e zıplıyor; Viterbi fizyolojik olarak makul yolu seçiyor.
> *Görsel:* `E_klasik_hard_s0.png` ile `E_ornek_hard_s0.png` yan yana.

### 10. Katkı 3: Bir hata avı, yumuşak cilt maskesi
- Klasik ikili maske, eşik sınırındaki pikseller yüzünden ışık titremesini **nabız sanıyor**.
- İkili maske denemelerin %100'ünde titremeye kilitleniyor (~33 BPM hata); zamanda yumuşatılmış ağırlıklı maske ile hata 0.1–0.2 BPM'e iniyor.
> *Görsel:* `results/maske_deneyi/maske_hata.png`.
> *Not:* Bu slayt "hata ayıklama hikâyesi" olarak anlatılırsa çok etkili olur.

### 11. Katkı 4: Kontrollü benchmark
9 senaryo, zorlukları tek tek aç/kapat.
> *Görsel:* B ablasyon ısı haritası.

### 12. Sonuçlar
- Sentetik: B tablosu, ORTALAMA sütunu
- UBFC: (doldurulacak)
- Kendi verimiz: koşul tablosu (doldurulacak)
- Bland-Altman grafiği

### 13. Klasik ve derin öğrenme karşılaştırması
rPPG-Toolbox TS-CAN ile bizim POS hattımız, UBFC üzerinde.
> *Not:* "Klasik yöntem açıklanabilir, eğitim gerektirmez ve CPU'da gerçek zamanlı çalışır."

### 14. Sınırlamalar
- Büyük baş hareketi, cilt tonu (Nowara 2020), otomatik pozlama, referans cihazın kendi hatası
- Sentetik sonuçlar gerçek veriden iyimserdir.

### 15. Gelecek çalışmalar
HRV (tepe tespiti ile RR aralıkları), SpO2 (iki dalga boyu), mobil uygulama.

### 16. Canlı demo + EVM
Kamera açık; `e` tuşu ile EVM. İzleyiciden bir gönüllü çağır ve akıllı saatiyle karşılaştır.

---

## Demo Kontrol Listesi
- [ ] Sunum bilgisayarında `CALISTIR.bat` → 1 çalışıyor mu?
- [ ] Işık: yüze önden, sabit (pencere karşısı veya masa lambası)
- [ ] Yedek plan: kamera çalışmazsa `CALISTIR.bat` → 2 (sentetik video demosu)
- [ ] Önceden kaydedilmiş bir EVM videosu masaüstünde hazır
