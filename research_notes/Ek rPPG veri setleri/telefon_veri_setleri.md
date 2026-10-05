# Smartphone-camera rPPG datasets (face video + fingertip video) with PPG/ECG ground truth

Scope: new smartphone datasets beyond the already-known MMPD, VIPL-HR, VitalVideos-Worldwide, MCD-rPPG, and MPU-rPPG. Checked October 2026. "Verified" means read on the official page or repo during this session. "Claimed" means it comes from a paper or a search snippet only.

## Which smartphone datasets contain face videos with PPG/ECG ground truth?

### Takeaway
Only one new smartphone face-video dataset with a PPG waveform turned up: **M³PD** (Tsinghua, arXiv Nov 2025). It has front-camera face video and rear-camera fingertip video recorded at the same time, from 60 subjects. Access needs a signed agreement sent by a faculty member, and the release is preprocessed 128×128 tensors, not raw video. ReViSe is a method paper; I found no public dataset for it. LADH and SUMS (same group) use webcams, not phones. Commercial or industry studies (Google, Binah.ai, NuraLogix, Lifelight) did not surface any public smartphone face-video data.

### Cited Findings
**M³PD (Dual-view Mobile PPG): new, verified**
- 60 subjects in total: 13 healthy lab participants (age 18–30) and 47 cardiovascular patients in a clinic (age 24–78) — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Phones: OPPO A52 in the lab, Xiaomi 14 in the clinic. The front camera records the face and the rear camera plus LED flash records the fingertip, simultaneously, both handheld. Recordings were 1280×720 at 30 fps. Lab segments are about 5.3 s (160 frames); clinic recordings are about 30 s — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Ground truth: CMS50E PPG waveform at 20 Hz, HR/SpO₂ at 1 Hz, HKH11C respiration belt at 50 Hz, OMRON U726J cuff BP (spot readings) — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Sync: the phone and the Windows PC were synced to the same NTP server. There is no hardware sync, so expect a timestamp offset of up to tens of ms or more — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Lab protocol had five phases: baseline, breath-hold, recovery, leg lifts, rest. Clinic recordings have no posture constraints and include tremor and hand shake — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Classical methods do badly on the handheld face videos: MAE of 16.5–32.9 BPM with near-zero correlation — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- License is CC BY 4.0, but access is by request under a non-commercial data-use agreement. Eye regions of patients must be blurred in publications — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)
- Access procedure (verified on the repo, [github.com/Health-HCI-Group/F3Mamba](https://github.com/Health-HCI-Group/F3Mamba)):
  - Sign the release agreement.
  - A **faculty member** (not a student) emails it to tjk24@mails.tsinghua.edu.cn, cc yuntaowang@tsinghua.edu.cn. The email includes the institution website, publications, and the intended use. The subject line in the README says "LADH Access Request - institution", which looks like a copy-paste from LADH.
  - Links (OneDrive / Baidu Netdisk) are sent after approval.
  - The data is **PyTorch .pth tensors at 128×128, 30 fps**, organized per participant, with BVP, HR, RR, SpO₂, and BP labels.
- Conflict: the paper says capture was 1280×720, but the repo distributes 128×128 tensors. Raw video does not appear to be released — [paper](https://arxiv.org/html/2511.02349) vs [repo](https://github.com/Health-HCI-Group/F3Mamba)

**ReViSe (Remote Vital Signs, smartphone): no public dataset found**
- The paper validates on the public TokyoTech rPPG and PURE datasets (webcams). Its own "Video-HR" and "Video-BP" sets were collected in daily-living settings, but the abstract and summary give no subject count, phone model, or availability statement, and no URL — [arXiv 2206.08748](https://arxiv.org/abs/2206.08748)

**LADH and SUMS (Tsinghua): not smartphone**
- LADH has 240 synchronized RGB+IR face videos from 21 participants over 10 days, with PPG, respiration, and SpO₂ — [arXiv 2506.09718](https://arxiv.org/pdf/2506.09718); repo at [McJackTang/FusionVitals](https://github.com/McJackTang/FusionVitals)
- Both LADH and SUMS use Logitech C922-type webcams, not phones. SUMS records face and fingertip views in a highland hypoxia setting — [search summary of arXiv 2506.09718](https://arxiv.org/pdf/2506.09718) (claimed, not checked in the PDF)

**Google smartphone-camera heart studies**
- Google Research has a blog post on passive heart monitoring via smartphone camera — [Google Research blog](https://research.google/blog/towards-passive-heart-health-monitoring-via-smartphone-camera/). I did not fetch it, and nothing I found indicates a public dataset.

### Inferences
- For face-video training on mobile, M³PD is the only new candidate. It is valuable because it is handheld, uses a real phone front camera, and includes older and cardiovascular patients. Two problems for this project's pipeline: the data is already cropped and resized to 128×128 tensors, so it won't match our own face-crop step, and the reference is 20 Hz CMS50E with NTP-only sync. Check polarity and lag before using it, as was done for MCD.
- Requests have to come from a faculty member, so a student needs their supervisor to send the email.

### Gaps
- None of the candidate names in the brief ("FaceRPPG", "MobilePhys", "PhysPhone", "SPAD", "BEAM", "TrueFace", "MAHNOB smartphone") produced a matching smartphone dataset in these searches. They may not exist or may be private. I ran only a limited number of searches.
- No public datasets were found from Binah.ai, NuraLogix, or Lifelight/Xim. These are presumed proprietary (unverified).
- M³PD total download size was not stated.

## Smartphone fingertip-video datasets (rear camera + flash) for finger mode

### Takeaway
Three fingertip datasets are fully open with no agreement: **BUT PPG** (PhysioNet, CC BY 4.0, ECG reference), **MTHS** (GitHub, iPhone 5s, HR/SpO₂ labels only), and **UW oximetry-phone-cam-data** (MIT, 6 subjects, raw MP4). BUT PPG and MTHS ship only frame-averaged signals, not raw video. The UW set is the only open one with raw finger videos, but it is small and very low resolution. M³PD's rear-camera fingertip videos are a fourth source, available by request.

### Cited Findings
**BUT PPG (Brno University of Technology), PhysioNet: verified**
- v2.0.0 was released 23 Aug 2024 (v1.0.0 on 18 Jan 2021). It has 3,888 10-second recordings from 50 subjects (25 F / 25 M) — [PhysioNet BUT PPG 2.0.0](https://physionet.org/content/butppg/2.0.0/)
- Phones are a Xiaomi Mi9 and a Huawei P20 Pro. About half the recordings are finger on the rear camera with LED, and half are ear on the front camera — [PhysioNet](https://physionet.org/content/butppg/2.0.0/)
- Ground truth is ECG from a Bittium Faros 360/180 at 1000 Hz, with QRS annotations. v2 adds accelerometer at 100 Hz, BP, glycaemia, and SpO₂ — [PhysioNet](https://physionet.org/content/butppg/2.0.0/)
- Data format is a 30 Hz PPG signal made by averaging each frame (red channel). **Raw video does not appear to be included** — [PhysioNet](https://physionet.org/content/butppg/2.0.0/)
- Signal quality: in the extension, 31% of finger signals and 11% of ear signals are rated good quality. The extension added 3,840 signals from 38 subjects aged 19–76 — [CinC 2024 extension paper](https://www.cinc.org/archives/2024/pdf/CinC2024-055.pdf)
- License is CC BY 4.0, **open access with no agreement**. Size is 203 MB uncompressed, 87 MB as ZIP — [PhysioNet](https://physionet.org/content/butppg/2.0.0/)

**MTHS (from the MEDVSE paper): open on GitHub, claimed via search**
- 62 subjects (35 M / 27 F). Index fingertip on the camera with flash, iPhone 5s, 30 fps. Labels are HR and SpO₂ at 1 Hz from an M70 pulse oximeter — [Healthcare Tech Letters 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13158377/); [arXiv 2204.08989](https://arxiv.org/pdf/2204.08989)
- Format is per subject `signal_x.npy` (mean R, G, B at 30 Hz) plus `label_x.npy`. There is **no raw video and no PPG waveform reference, only 1 Hz HR/SpO₂** — [MEDVSE README](https://github.com/MahdiFarvardin/MEDVSE/blob/main/README.md)
- Hosted at [github.com/MahdiFarvardin/MEDVSE](https://github.com/MahdiFarvardin/MEDVSE). The old URL github.com/MahdiFarvardin/MTHS returns 404 (verified). I did not check the license file.

**UW smartphone camera oximetry (Hoffman et al., npj Digital Medicine 2022): verified**
- 6 healthy subjects in an induced-hypoxemia (varied FiO₂) protocol with SpO₂ from 70% to 100%. One finger from each hand was on a Google Nexus 6P camera with flash. Video was 30 fps at 176×144 — [PMC9483471](https://pmc.ncbi.nlm.nih.gov/articles/PMC9483471/)
- Reference is four clinical pulse oximeters (Masimo Radical-7, Nellcor N-600X, and others) at 1 Hz — [GitHub repo](https://github.com/ubicomplab/oximetry-phone-cam-data)
- The repo has raw MP4 videos (separate link) plus per-frame RGB-mean CSVs. **MIT license, fully open** — [GitHub repo](https://github.com/ubicomplab/oximetry-phone-cam-data)

**M³PD rear-camera fingertip videos**
- Recorded at the same time as the face video, on handheld OPPO A52 and Xiaomi 14 phones with LED flash. Reference is CMS50E PPG at 20 Hz. Access needs a faculty agreement (see above) — [arXiv 2511.02349](https://arxiv.org/html/2511.02349)

**Not usable / not public**
- EkaCare (India): 7,409 subjects, fingertip on the rear camera for 40 s, reference Dr Trust 203 pulse oximeter. The paper has no data-availability statement for public release — [PMC11844976](https://pmc.ncbi.nlm.nih.gov/articles/PMC11844976/)
- "Your smartphone could act as a pulse-oximeter and as a single-lead ECG" (Sci Rep 2023): fingertip on the rear camera. Dataset size and availability were not confirmed because the Nature page redirected to a login — [arXiv 2305.12583](https://arxiv.org/abs/2305.12583)

### Inferences
- For finger mode, BUT PPG is the best open source with a beat-accurate reference (1000 Hz ECG + QRS). It is a good test bench for a signal-domain finger-mode HR estimator, meaning frame-mean in and HR out, which matches what a browser finger mode computes. It cannot train a pixel-level model.
- MTHS is useful only for 1 Hz HR regression on RGB-mean traces.
- The UW set is the only open source of raw finger video. It is too small to train on and is best used as a sanity check.

### Gaps
- Exact smartphone resolution for BUT PPG and per-recording metadata were not checked in the files.
- MTHS license not verified.
- Data availability for the Sci Rep 2023 (Pakistan) finger dataset is unverified.

## Which are fully open (no agreement)? Ranking

### Takeaway
None of the new **face-video** smartphone datasets are fully open. M³PD needs a faculty-signed agreement. The fully open new items are all fingertip datasets.

### Cited Findings
Ranking for this project (mobile-browser HR model), new items only:
1. **BUT PPG v2.0.0**: fully open, CC BY 4.0, 87 MB, ECG reference, two Android phones, finger and ear. Signals only, no video — [PhysioNet](https://physionet.org/content/butppg/2.0.0/)
2. **UW oximetry-phone-cam-data**: fully open, MIT, raw finger MP4s. Only 6 subjects, 176×144, 1 Hz reference — [GitHub](https://github.com/ubicomplab/oximetry-phone-cam-data)
3. **MTHS (MEDVSE repo)**: open on GitHub. 62 subjects, RGB-mean signals, 1 Hz HR/SpO₂ only — [GitHub](https://github.com/MahdiFarvardin/MEDVSE)
4. **M³PD**: on request (faculty-signed DUA, non-commercial). It is the **only new smartphone face-video set** and has handheld front and rear dual view, but ships as 128×128 tensors — [GitHub F3Mamba](https://github.com/Health-HCI-Group/F3Mamba)
- Known datasets were not re-researched. For context, MPU-rPPG is on Figshare (doi 10.6084/m9.figshare.29377835) — [Nature Sci Data](https://www.nature.com/articles/s41597-026-07310-3) — and VitalVideos-Worldwide is by license on request — [HF](https://huggingface.co/datasets/pjtoye/VitalVideos-Worldwide).

### Inferences
- The face-model work can most realistically add M³PD, if a faculty supervisor can request it. On the open side, BUT PPG is the strongest finger-mode benchmark.

### Gaps
- No open mirror (Kaggle, HF, Zenodo) of M³PD or of any new smartphone face dataset was found. A Kaggle "rPPG Dataset" (ashfakyeafi) appeared in results but was not checked.
