"""
rppg — Klasik görüntü işleme tabanlı temassız nabız (rPPG), solunum ve
Eulerian Video Magnification (EVM) araç seti.

Sayısal Görüntü İşleme dönem projesi — Hayrunnisa Güven, Fırat Üniversitesi.

Modüller
--------
roi          : Yüz tespiti (Viola-Jones Haar), şablon eşleme ile takip,
               ROI tanımları, YCrCb cilt maskesi + morfoloji
signals      : Videodan ROI başına ortalama RGB izlerinin çıkarılması,
               hareket indeksi, göğüs bölgesinde optik akış
filtering    : Tarvainen detrend, Butterworth bant geçiren filtre
methods      : GREEN, ICA, CHROM, POS, LGI rPPG yöntemleri
hr           : Spektrum, SNR, kayan pencere spektrogramı, Viterbi takibi
fusion       : (Özgün) SNR ağırlıklı çoklu-ROI spektral füzyon +
               hareket farkında güven ağırlığı
pipeline     : Uçtan uca tahmin (Config -> Result)
respiration  : Optik akış tabanlı solunum hızı
evm          : Renk büyütme (çevrimdışı FFT ve çevrimiçi IIR sürümleri)
metrics      : MAE, RMSE, MAPE, Pearson r, Bland-Altman
synthetic    : Kontrollü zorluk senaryolu sentetik yüz videosu üreteci
io_utils     : Video okuma, UBFC-rPPG ve kendi kayıtlarımız için yükleyiciler
evaluation   : Çoklu konfigürasyon değerlendirme (ablasyon)
plotting     : Rapor şekilleri
"""

__version__ = "1.0.0"
