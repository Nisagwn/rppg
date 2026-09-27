# Dönem Projesi Önerisi

**Ders:** Sayısal Görüntü İşleme
**Öğrenci:** Hayrunnisa Güven — Yazılım Mühendisliği, Fırat Üniversitesi
**Proje adı:** *Kamerayla Temassız Nabız ve Solunum Ölçümü: Klasik Görüntü İşleme ile Çoklu Bölge Füzyonu ve Hareket Farkında Spektral Takip*

---

## 1. Problem ve Motivasyon

Kalp atışıyla deri altındaki kan hacmi periyodik olarak değişir. Hemoglobin ışığı soğurduğu için bu değişim yüz derisinin renginde çok küçük (piksel değerinde ~0.1–0.5 gri seviye) dalgalanmalara yol açar. Bu dalgalanmalar gözle görülmez ama bir video üzerinde **uzamsal ortalama, renk uzayı projeksiyonu ve frekans analizi** ile ölçülebilir. Bu tekniğe uzaktan fotopletismografi (**rPPG**) denir.

Temassız ölçüm yenidoğan yoğun bakımı, yanık hastaları, uzaktan sağlık (tele-tıp) ve sürücü yorgunluğu takibi gibi alanlarda kullanılabilir.

Bu proje, dersin konularını **tek bir uçtan uca sistemde** uygulamak için iyi bir örnek. Derin öğrenme merkezde değil; her aşama klasik görüntü ve sinyal işleme ile çözülüyor.

## 2. Amaçlar

1. Webcam videosundan **nabız (BPM)** ve **solunum hızını (nefes/dk)** ölçen, gerçek zamanlı çalışan bir sistem geliştirmek.
2. Literatürdeki beş klasik rPPG yöntemini (**GREEN, ICA, CHROM, POS, LGI**) aynı hat içinde uygulayıp karşılaştırmak.
3. Üç özgün iyileştirme önermek ve ablasyon ile etkilerini ölçmek:
   - **SNR ağırlıklı çoklu-ROI spektral füzyon**
   - **Hareket farkında güvenle ölçeklenen Viterbi HR takibi**
   - **Kontrollü zorluk senaryolu sentetik benchmark**
4. **Eulerian Video Magnification (EVM)** ile nabzı videoda görünür hale getirmek.

## 3. Kullanılacak Görüntü İşleme Teknikleri

| Ders konusu | Projedeki karşılığı |
|---|---|
| Nesne tespiti, öznitelik tabanlı sınıflandırıcı | Viola-Jones Haar kaskad ile yüz tespiti |
| Şablon eşleme, korelasyon | NCC ile yüz takibi, alt-piksel tepe konumu |
| Renk uzayları | YCrCb cilt segmentasyonu, RGB→krominans (CHROM), POS düzlemi, YIQ (EVM) |
| Eşikleme, segmentasyon | YCrCb aralık eşikleme ile cilt maskesi |
| Morfolojik işlemler | Maske üzerinde açma ve kapama |
| Uzamsal filtreleme | Gauss piramidi (EVM), ROI içinde uzamsal ortalama (alçak geçiren) |
| Frekans domeni | FFT ve periyodogram, ideal bant geçiren (EVM), spektrogram |
| Filtre tasarımı | Butterworth bant geçiren, sıfır fazlı filtre, IIR (canlı EVM) |
| Hareket analizi | Farnebäck yoğun optik akış (solunum), kare farkı (hareket indeksi) |
| Görüntü piramitleri | Laplacian/Gauss piramidi (EVM) |
| Öznitelik çıkarımı | ROI renk izleri, spektral SNR, hareket indeksi |

## 4. Veri

| Kaynak | Açıklama | Kullanım |
|---|---|---|
| **UBFC-rPPG** (Bobbia vd.) | 42 denek, 640×480, 30 fps, sıkıştırılmamış video ve eşzamanlı oksimetre PPG'si | Ana değerlendirme |
| **Kendi kayıtlarımız** | 5–10 gönüllü, 7 koşul (gün ışığı, floresan, loş ışık, ekran ışığı, konuşma, baş hareketi, egzersiz sonrası); referans olarak parmak oksimetre ya da akıllı saat | Gerçek dünya testi |
| **Sentetik benchmark** | 9 senaryo, bilinen HR ve solunum, zorluklar tek tek açılıp kapatılabiliyor | Kontrollü ablasyon |

## 5. Değerlendirme Metrikleri

- **MAE, RMSE** (BPM) ve **MAPE** (%)
- **Pearson r**
- **Bland-Altman** analizi (yanlılık ve %95 uyum sınırları)
- **≤5 BPM oranı** (pencerelerin yüzdesi)
- Solunum için MAE (nefes/dk)
- Canlı sistem için FPS

## 6. Hibrit (Klasik + Derin Öğrenme) Karşılaştırması

Aynı UBFC videolarında rPPG-Toolbox'ın önceden eğitilmiş derin modelleri (PhysNet, TS-CAN) çalıştırılacak ve sonuçlar önerilen klasik hatla karşılaştırılacak. Araştırma sorusu şu: *"Klasik ve açıklanabilir bir hat hangi koşullarda derin modellere yetişiyor ve hangi koşullarda geride kalıyor?"*

## 7. Beklenen Çıktılar

- Açık kaynak Python kütüphanesi ve canlı demo
- Kendi toplanan, etiketli küçük veri seti
- Ablasyon tabloları, Bland-Altman grafikleri, EVM videoları
- Dönem raporu ve sunum

## 8. Riskler ve Önlemler

| Risk | Önlem |
|---|---|
| Webcam otomatik pozlaması sinyali bozar | Kilitleme denenir; gerçek değer meta veriye yazılır |
| FPS dalgalanması | Zaman damgasıyla sabit 30 Hz'e yeniden örnekleme |
| Hareket artefaktları | Hareket farkında güven ve Viterbi takibi |
| Etik ve KVKK | Anonim kodlar, onam formu, yüz videoları paylaşılmaz |
| UBFC'ye erişilemezse | Sentetik benchmark ve kendi verimiz |

Haftalık iş planı için bkz. [`04_is_plani.md`](04_is_plani.md).
