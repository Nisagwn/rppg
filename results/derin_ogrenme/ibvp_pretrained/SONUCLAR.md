# Hazır iBVP-FactorizePhys / mevcut uygulama modeli

11 Kasım 2026. Yeni eğitim yapılmadı; rPPG-Toolbox'ın hazır iBVP ağırlıkları sınandı.

## Karar

Hazır iBVP ağırlıkları bu projenin test hattında mevcut tur5 modelini geçmedi. Resmî ağ ayarlarıyla da dikkat modülü açık ek kontrolde de telefon/yan kamera hatası daha yüksek. Uygulama için mevcut model tercih edilir. Bu sonuç iBVP verisiyle yapılacak gelecekteki ince ayarın sonucunu veya veri setinin genel değerini belirlemez.

## Sonuç: aynı kayıtlar, hop=80 (%50 örtüşme), Viterbi

| Model                        |   Ana MAE (BPM) |   Telefon/USB MAE (BPM) |
|:-----------------------------|----------------:|------------------------:|
| Mevcut uygulama tur5         |           1.101 |                   1.592 |
| iBVP - resmî ağ ayarları     |           2.502 |                   8.698 |
| iBVP - dikkat açık (tanısal) |           2.502 |                   7.923 |

Ana grupta 8 UBFC test videosu ve 20 MCD önden webcam kaydı vardır: toplam 28. Bu, 42 kişilik UBFC değerlendirmesi değildir. Telefon/USB klasöründeki 40 kayıttan ortak yüz kalitesi filtresini geçen 28 kayıt kullanılır; 12 kayıt dışarıda kalır. Her videonun 10 saniyelik pencerelerindeki MAE hesaplanıp videolar eşit ağırlıkla ortalanır. Video-düzeyi spektral hata ayrıca alt raporlarda bulunur; iki ölçüt birbirine karıştırılmaz.

- [Resmî ağ profiliyle ayrıntılı sonuç](official_cpu/SONUCLAR.md)
- [Dikkat modülü açık tanısal kontrol](fsam_on_cpu/SONUCLAR.md)
- [Kaynak, commit ve checkpoint özeti](kaynak.json)

## Yapılandırma ve yorum sınırı

[Resmî YAML](https://github.com/ubicomplab/rPPG-Toolbox/blob/b7500b848f84ad7f86e277b4612563b69f4f88f9/configs/infer_configs/iBVP_UBFC-rPPG_FactorizePhys_FSAM_Res.yaml) `MD_FSAM=False`, 160 kare, 72×72 ham RGB, 30 fps kullanıyor. Ağ parametrelerimiz YAML ile karşılaştırılarak doğrulandı. Birincil koşuda aktif ağ için eksik ağırlık yok; checkpoint'teki devre dışı FSAM'a ait dört parametre kullanılmıyor. Bunlar `ayarlar.json` yükleme raporunda açıkça listelenir. Ek kontrolde yalnız `MD_FSAM=True` yapıldı; bu resmî profilden bilinçli bir sapmadır ve birincil sonuç gibi sunulmaz.

Kontrollü karşılaştırma mevcut **aynı Haar kırpıntıları** üzerinde yapıldı. Resmî YAML ise Y5F yüz bulucu ve bütün-video FFT değerlendirmesi içeriyor. Dolayısıyla bu deney yazarların tüm ön işleme/ölçüm protokolünün birebir yeniden üretimi değildir; adayın bizim mevcut hattımıza uygunluğunu ölçer. Mobil cihaz süresi ve canlı kullanıcı doğruluğu bu koşuda ölçülmedi.

## CPU ve önceki sonuçların kullanımı

Kullanıcı GPU kullanılmamasını istediğinde ilk CUDA süreçleri durduruldu; bu süreçlerden tamamlanmış rapor kullanılmadı. Buradaki iki aday koşusu CPU üzerinde yeniden çalıştırıldı; `CUDA_VISIBLE_DEVICES=-1` ve `--device cpu` kullanıldı. Birincil koşu 4, tanısal koşu 2 CPU iş parçacığı kullandı. Süreler model hızı kıyaslaması olarak raporlanmıyor.

Mevcut tur5 modelinin aynı dosya listesi ve hop için önceden kaydedilmiş sonuçları yeniden kullanıldı. Bu eski referansın orijinal aygıtı CUDA'dır; GPU isteğinden sonra yeniden CUDA işi başlatılmadı. Checkpoint SHA-256 değeri doğrulandı. İki kayıt CPU'da tekrar ölçülerek kontrol edildi: [CSV](baseline_cpu_check.csv), [özet](baseline_cpu_check.json). En büyük pencere-MAE farkı yaklaşık 0.000038 BPM. Bu iki kayıtlık bir doğrulamadır; bütün referans kümesinin CPU'da yeniden ölçüldüğü iddia edilmez.

## EMPD kullanıldı mı?

**Hayır. EMPD hiçbir eğitimde veya model testinde kullanılmadı.** Önceki araştırmada küçük global metadata, ilk PPG CSV örneği ve TAR başlıkları incelendi. Eğitim biçimine dönüştürülen RGB oturumları, veri yükleyicisi veya EMPD ile eğitilmiş model henüz yok.

[EMPD teknik incelemesi](../../../research_notes/veri_arastirmasi_2026_11_11/ARASTIRMA.md). Kullanıma almak ayrı bir veri hazırlama işidir: RGB/PPG'yi event dosyalarından ayrı seçerek indirme, zaman eşleşmesini doğrulama ve aynı kişinin farklı kayıtlarını tek bölmede tutma gerekir. Kayıt zamanından kişi kimliği türetilmemeli; `Participants` alanı kullanılmalı.

## Tekrar çalıştırma

```powershell
$env:CUDA_VISIBLE_DEVICES = '-1'
.venv/Scripts/python.exe scripts/compare_pure_candidate.py --device cpu --hops 80 --candidate external/rPPG-Toolbox/final_model_release/iBVP_FactorizePhys_FSAM_Res.pth --candidate-name "iBVP FactorizePhys official" --candidate-config configs/ibvp_factorizephys_official.json --out results/run/ibvp_cpu_repeat
```

Bu komut referans modeli de CPU'da yeniden hesaplar. Arşivlenen koşuda kullanılan doğrulanmış önbellek yolu, profil ve dosya listeleri `official_cpu/ayarlar.json` içindedir. Karşılaştırma betiğinin varsayılan aygıtı artık CPU'dur; başka aygıt ancak açıkça seçilirse kullanılır.
