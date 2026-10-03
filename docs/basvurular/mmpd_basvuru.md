# MMPD veri seti başvurusu

MMPD: 33 kişi, telefonla çekilmiş yüz videoları; 4 ışık koşulu (LED düşük/yüksek, akkor, doğal), 4 hareket durumu
(sabit, baş çevirme, konuşma, yürüme), Fitzpatrick 3–6 ten tonları ve PPG referansı. Mini sürümü 48 GB
(80×60 piksel), tam sürümü 370 GB.
Kaynak: https://github.com/McJackTang/MMPD_rPPG_dataset

## Şartlar

- E-postayı **öğretim üyesi** göndermeli; öğrenci başvurusu kabul edilmiyor.
- Gönderen adres **kurumsal** olmalı (`@firat.edu.tr`).
- [MMPD_Release_Agreement.pdf](https://github.com/McJackTang/MMPD_rPPG_dataset/blob/main/MMPD_Release_Agreement.pdf)
  doldurulup öğretim üyesi tarafından imzalanmalı ve e-postaya eklenmeli.
- Alıcı: **tjk24@mails.tsinghua.edu.cn**, bilgi (CC): **yuntaowang@tsinghua.edu.cn**
- Konu satırı tam olarak şu kalıpta olmalı: `MMPD Access Request - Firat University`
- Kullanım yalnızca akademik; ticari kullanım yasak.

## Hocaya iletilecek not

> Hocam merhaba, Sayısal Görüntü İşleme dersi kapsamındaki temassız nabız ölçümü (rPPG) projemde telefon kamerası
> için bir derin öğrenme modeli eğitiyorum. Modelin telefonda nasıl çalıştığını ölçebilmek için Tsinghua
> Üniversitesi'nin MMPD veri setine ihtiyacım var. Veri seti yalnızca öğretim üyesi başvurusuyla veriliyor. Aşağıdaki
> e-postayı ve imzalı sözleşme formunu kurumsal adresinizden gönderebilir misiniz? Formu sizin için doldurup
> hazırlayabilirim.

## E-posta taslağı (hoca gönderir)

**To:** tjk24@mails.tsinghua.edu.cn
**CC:** yuntaowang@tsinghua.edu.cn
**Subject:** MMPD Access Request - Firat University
**Attachment:** MMPD_Release_Agreement (signed).pdf

> Dear Mr. Tang and Prof. Wang,
>
> I am [title and full name], a faculty member in the Department of Software Engineering at Firat University,
> Türkiye ([department web page]). I would like to request access to the MMPD dataset for academic research and
> teaching. The signed release agreement is attached.
>
> The dataset will be used in an undergraduate research project I supervise (student: Hayrunnisa Güven) on
> camera-based remote photoplethysmography for smartphones. We have fine-tuned FactorizePhys (rPPG-Toolbox) on
> MCD-rPPG, UBFC-rPPG and PURE. These datasets are recorded with webcams, while our application runs in a mobile
> browser. We would use MMPD to:
>
> 1. evaluate the model on mobile-phone videos under different lighting, motion and skin-tone conditions, and
> 2. fine-tune the model for mobile capture, using a subject-disjoint split.
>
> The mini version (80×60) would be sufficient for our needs. The data will be kept on the project computers.
> Training runs in a private cloud GPU session (Kaggle), where the data is held only temporarily and deleted when the
> session ends. Please let us know if this is not permitted under the agreement. The data will be used only for
> non-commercial research and will not be redistributed. Any publication will cite the MMPD
> paper (Tang et al., EMBC 2023).
>
> [Relevant publications, if any]
>
> Thank you for considering our request.
>
> Best regards,
> [Name, title]
> Department of Software Engineering, Firat University
> [institutional e-mail, phone]

## Sonra

Erişim gelince `scripts/dl_prepare.py`'a MMPD okuyucusu eklenecek. Kişilerin bir kısmı telefon testi olarak
ayrılacak (eğitime hiç girmeyecek), kalanı eğitime eklenecek.
