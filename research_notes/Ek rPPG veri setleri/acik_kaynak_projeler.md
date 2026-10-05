# Open-source rPPG projects: which datasets they use and how to get them (checked 2026-10-05)

Datasets we already use and therefore leave out of the "new" lists: MCD-rPPG, UBFC-rPPG, PURE, UBFC-Phys, MMPD, VIPL-HR, COHFACE, VitalVideos, MPU-rPPG, SCAMPS.

## Q1. Which dataset loaders/configs does each project have, and what download instructions does it give?

### Takeaway
rPPG-Toolbox is the main reference. Besides datasets we already use, it now has loaders for BP4D+, iBVP, PhysDrive, SUMS and LADH. pyVHR and remotebiosensing/rppg add older datasets: LGI-PPGI, MAHNOB-HCI, ECG-Fitness, VicarPPG-2, V4V, MMSE-HR, MR-NIRP, OBF, MTHS and others. PhysBench adds RLAP. None of these repos ships data. Every one sends users to the dataset owner, usually with a signed agreement.

### Cited Findings
**rPPG-Toolbox (ubicomplab)**
- `dataset/data_loader/` contains BP4DPlusLoader, BP4DPlusBigSmallLoader, COHFACELoader, LADHLoader, MMPDLoader, PURELoader, PhysDriveLoader, SCAMPSLoader, SUMSLoader, UBFCPHYSLoader, UBFCrPPGLoader and iBVPLoader — [GitHub tree](https://github.com/ubicomplab/rPPG-Toolbox/tree/main/dataset/data_loader)
- README download routes: MMPD at github.com/McJackTang/MMPD_rPPG_dataset; SCAMPS at github.com/danmcduff/scampsdataset; UBFC-rPPG and UBFC-Phys at sites.google.com/view/ybenezeth; PURE by request to TU Ilmenau; BP4D+ "by emailing the authors" (Binghamton 3DFE page); iBVP at github.com/PhysiologicAILab/iBVP-Dataset; PhysDrive at github.com/WJULYW/PhysDrive-Dataset; SUMS at github.com/thuhci/SUMS; LADH at github.com/McJackTang/FusionVitals — [rPPG-Toolbox README](https://github.com/ubicomplab/rPPG-Toolbox)
- The README does not mention any shared preprocessed cache. Users download the raw data and preprocess it with the toolbox — [rPPG-Toolbox README](https://github.com/ubicomplab/rPPG-Toolbox)

**PhysBench (KegangWangCCNU)**
- The current repo says "Full release coming soon" and lists no datasets — [PhysBench](https://github.com/KegangWangCCNU/PhysBench)
- The archived version benchmarks RLAP (58 subjects, 3.53M frames, MJPG), RLAP-rPPG (58 subjects, 781K frames, lossless), PURE, UBFC-rPPG, UBFC-Phys, MMPD, COHFACE and SCAMPS. It gives only paper citations for every dataset except RLAP — [PhysBench_Archived](https://github.com/KegangWangCCNU/PhysBench_Archived)
- RLAP (Remote Learning Affect and Physiology): 58 students, more than 32 h of video, Logitech C930c webcam plus CMS50E oximeter, released as an ISO image. To get it, email kegangwang@mails.ccnu.edu.cn, cc yantaowei@ccnu.edu.cn, and attach the signed Data Usage Agreement — [RLAP-dataset repo](https://github.com/KegangWangCCNU/RLAP-dataset) (search snippet); [PhysBench_Archived](https://github.com/KegangWangCCNU/PhysBench_Archived)

**pyVHR (phuselab)**
- Has interfaces for COHFACE, LGI-PPGI, MAHNOB-HCI, PURE, UBFC1, UBFC2, UBFC-Phys, ECG-Fitness, Vicar-PPG-2 (via a Google Form), V4V and VIPL-HR. Links: LGI-PPGI at github.com/partofthestars/LGI-PPGI-DB; MAHNOB at mahnob-db.eu/hci-tagging; ECG-Fitness at cmp.felk.cvut.cz/~spetlrad/ecg-fitness; V4V at vision4vitals.github.io — [pyVHR](https://github.com/phuselab/pyVHR)

**remotebiosensing/rppg**
- Its dataset table lists 25 datasets. Those not yet in our set:
  - MAHNOB-HCI (27 subjects, ECG; mahnob-db.eu)
  - AFRL (25 subjects; no link)
  - BP4D+ (140 subjects)
  - MMSE-HR (40 subjects; licensed through binghamton.technologypublisher.com)
  - LGGI/LGI-PPGI (25 subjects)
  - OBF (100 subjects, RGB/NIR, ECG; no link)
  - MR-NIRP indoor (8 subjects) and MR-NIRP driving (18 subjects), both at computationalimaging.rice.edu/mr-nirp-dataset
  - VicarPPG (10 subjects; Google Form)
  - MPSC-rPPG (9 subjects; IEEE DataPort)
  - V4V (140 subjects)
  - MTHS (62 subjects, smartphone; no link)
  - EatingSet, StableSet, BSIPL-RPPG and BAMI-rPPG (no links)
  - DEAP

  The table also lists UBFC-Phys at "ieee-dataport.org/open-access/ubfc-phys-2" and Vital Videos via a Dropbox link — [remotebiosensing/rppg README](https://raw.githubusercontent.com/remotebiosensing/rppg/main/README.md)

**contrast-phys / contrast-phys+ (zhaodongsun)**
- Uses UBFC-rPPG as its example. It gives no dataset download links, only a OneDrive link to one example .h5 file and a Windows OpenFace build. Contrast-phys+ adds no dataset information — [contrast-phys](https://github.com/zhaodongsun/contrast-phys)

**Deep-rPPG (terbed)**
- Uses a private neonatal dataset from Semmelweis University with no access route, and no public benchmarks — [Deep-rPPG](https://github.com/terbed/Deep-rPPG)

**New datasets reached through those repos (details)**
- **iBVP**: 31 participants (7 with restricted use), 124 sessions of 3 min, RGB (Logitech BRIO, 640x480 at 30 fps) plus thermal (FLIR A65SC), PPG with quality labels, about 400 GB compressed. Academic use only. Requires a EULA signed by an academic supervisor, emailed to J. Joshi and Y. Cho — [iBVP-Dataset](https://github.com/PhysiologicAILab/iBVP-Dataset)
- **PhysDrive** (NeurIPS 2025): 48 subjects, about 24 h and 1.5M frames, RGB, NIR and mmWave in a car. Labels: ECG, BVP, respiration, HR, RR and SpO2. Academic use only. Raw data needs a sharing agreement (xyang856@connect.hkust-gz.edu.cn). A preprocessed subset is on Kaggle: one subject's RGB/NIR plus everyone's mmWave — [PhysDrive-Dataset](https://github.com/WJULYW/PhysDrive-Dataset)
- **SUMS**: 10 subjects at high altitude, 80 face and finger videos (Logitech C922, 1280x720 at 60 fps), PPG at 20 Hz, RR and SpO2. A faculty member must sign the release agreement and send it from an institutional email to tjk24@mails.tsinghua.edu.cn — [SUMS](https://github.com/thuhci/SUMS)
- **LADH** (FusionVitals): 21 subjects, 240 RGB+IR videos (640x480 at 30 fps), PPG, SpO2 and RR, 133.22 GB. Same Tsinghua agreement process. Delivered via OneDrive or Baidu — [FusionVitals](https://github.com/McJackTang/FusionVitals)
- **LGI-PPGI**: 25 subjects, 100 videos, about 200 min (Logitech C270 at 25 fps, uncompressed), CMS50E reference, CC-BY-4.0. Only sessions 1–6 (about 35.6 GB) have direct links at gw.cancontrols.com/LGI_DATABASE/. The other 19 are "t.b.c." — [LGI-PPGI-DB](https://github.com/partofthestars/LGI-PPGI-DB)
- **DLCN** (dynamic lighting at night, arXiv:2507.04306): 98 participants, 8 sequences each (rest/exercise × 4 lighting conditions). The processed .h5 files are openly on Kaggle (see Q3). Raw videos need an emailed release agreement (zhipengli@stu.cqut.edu.cn / hgxiao@cqut.edu.cn) — [DLCN GitHub](https://github.com/dalaoplan/DLCN); [Kaggle](https://www.kaggle.com/datasets/dalaoplan/rppg-dlcn)
- **BH-rPPG**: 12 subjects, 36 videos (3 lighting levels, about 20 fps, 900 frames each, uncompressed), CMS50E reference. Research use only. Request it from yangze@buaa.edu.cn using an institutional email; Gmail is not accepted — [BH-rPPG-dataset](https://github.com/yangze68/BH-rPPG-dataset)
- **rPPG-10**: 26 subjects, 10-minute videos (Microsoft webcam, 1280x720 at 30 fps) in uncontrolled daylight. The reference is ECG (BITalino, 1000 Hz), not PPG. CC BY, openly downloadable from Mendeley Data (DOI 10.17632/bx8982xgwt.1) — [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12311941/); [Mendeley](https://data.mendeley.com/datasets/bx8982xgwt/1)

### Inferences
- The only new datasets that can be downloaded right now with no agreement are DLCN (processed h5 on Kaggle), rPPG-10 (Mendeley, CC BY, but ECG reference), LGI-PPGI sessions 1–6 (CC-BY), and probably ECG-Fitness, MR-NIRP and UBFC-Phys on DataPort (their hosting pages are listed but I did not test the downloads).
- iBVP, RLAP, SUMS, LADH, PhysDrive (raw) and BH-rPPG all need an agreement signed by a faculty member or institution. RLAP (58 subjects, more than 32 h, webcam with CMS50E) and iBVP (high-quality PPG labels) are the strongest additions for a webcam/phone model.
- Since rPPG-Toolbox already has loaders for iBVP, PhysDrive, SUMS and LADH, they can be used for format reference if we get access.

### Gaps
- I did not check the READMEs of PhysNet/PhysFormer (ZitongYu), RhythmFormer, PhysMamba, the FactorizePhys repo, TS-CAN/EfficientPhys/BigSmall/MTTS-CAN, yarppg or Open-rPPG individually. From memory (unverified): they use the same benchmarks (UBFC, PURE, MMPD, VIPL, iBVP, SCAMPS, BP4D+), and the FactorizePhys paper uses iBVP, PURE, UBFC-rPPG and SCAMPS.
- The RLAP repo page itself was not fetched; its access terms come from the archived PhysBench README and a search snippet.
- The ECG-Fitness and UBFC-Phys DataPort pages returned HTTP 200, but downloads were not tested. The LGI direct link did not answer a HEAD request, so its status is unverified.

## Q2. Do any repos host or link data directly (Drive, Baidu, OneDrive, Zenodo, HF), or share preprocessed caches?

### Takeaway
None of the major repos hosts benchmark data. They link only to original owners or request forms, plus a single example .h5 from contrast-phys. Hugging Face, however, has many user re-uploads, mostly copies of MCD-rPPG and UBFC. Their licences are unclear.

### Cited Findings
- contrast-phys shares one example .h5 file and an OpenFace build, both via OneDrive — [contrast-phys](https://github.com/zhaodongsun/contrast-phys)
- remotebiosensing/rppg links Vital Videos through a public Dropbox share — [README](https://raw.githubusercontent.com/remotebiosensing/rppg/main/README.md)
- LADH is delivered via OneDrive/Baidu after approval — [FusionVitals](https://github.com/McJackTang/FusionVitals)
- HF API search for "rppg" (2026-10-05) returns many `*/mcd_rppg` mirrors, e.g. akramic, wengziheng, dypknu (gated "auto") and others. Other results: `thachha901/UBFC` (a raw UBFC-rPPG copy: subjectN/vid.avi + ground_truth.txt, no licence, 4,120 downloads); `WeiQian98/UBFC-rPPG` (gated manual); `Horusprg/UBFC-rPPG-Faces`; `jjuik2014/UBFC-Phys-all` (gated; its file list actually starts with MAFW files); `Bgeorge/RPPG` (MediaPipe-preprocessed MCD npz plus models, cc-by-nc-sa-2.0); `capruxel/thenar-rppg-hr-2026` (only derived thenar/palm RGB-NIR signals, cc-by-nc-4.0, no raw video); `NetherlandsForensicInstitute/rppg-deepfake-detection` (real and fake face videos for deepfake detection); `1Li/DLCN-rPPG` (README only, empty) — [HF API](https://huggingface.co/api/datasets?search=rppg)
- The original MCD-rPPG is at huggingface.co/datasets/kyegorov/mcd_rppg — [HF](https://huggingface.co/datasets/kyegorov/mcd_rppg)

### Inferences
- HF and Kaggle re-uploads of licensed datasets (UBFC, UBFC-Phys) are user copies, not the official channel. Use the official route for anything publishable.
- I found no open HDF5 or preprocessed cache of PURE, VIPL, iBVP or RLAP.

### Gaps
- I found no Zenodo-hosted rPPG benchmark in these repos. I did not run a dedicated Zenodo search.

## Q3. Kaggle: rPPG datasets with video + PPG (licence, size)

### Takeaway
Two Kaggle datasets are genuinely new to us: DLCN (98 subjects, processed h5, 42.8 GB, CC BY-NC-SA 4.0) and "ashfakyeafi/rppg-dataset" (MOV video plus Empatica E4 BVP, 4.4 GB, licence unknown, origin unclear). The rest are mirrors or derivatives of UBFC-rPPG, UBFC-Phys, MMPD or MCD.

### Cited Findings (Kaggle public API `/api/v1/datasets/list?search=…` and `/datasets/view/…`, queried 2026-10-05)
- `dalaoplan/rppg-dlcn`, "rPPG dataset under dynamic lighting conditions at night": 42.77 GB, CC BY-NC-SA 4.0, updated 2025-05-27, 336 downloads. Files are per-subject h5 (`DLCN/P10_1.h5` … `_8`). Its description says an agreement is required, pointing to github.com/dalaoplan/DLCN — [Kaggle](https://www.kaggle.com/datasets/dalaoplan/rppg-dlcn)
- `ashfakyeafi/rppg-dataset`: 4.38 GB, licence "Unknown", 2022, 3,018 downloads. Each subject has `trial_001/video/video.MOV` (about 540 MB) and `empatica_e4/BVP.csv, HR.csv, IBI.csv, EDA.csv, ACC.csv, TEMP.csv`. No description is given — [Kaggle](https://www.kaggle.com/datasets/ashfakyeafi/rppg-dataset)
- `malekdinarito/ubfc-rppg-dataset`: a UBFC-rPPG mirror, 33.5 GB (the view API reports 73.4 GB total bytes), labelled CC0, 4,393 downloads. Also `hiyorindm/ubfc-rppg-2` (33.5 GB) and `ashfakyeafi/ubfc-2` (12.95 GB) — [Kaggle](https://www.kaggle.com/datasets/malekdinarito/ubfc-rppg-dataset)
- UBFC-Phys mirrors: `hcmuehmduck/ubfc-phys` (212.6 GB, licence unknown, 2,282 downloads), `phanquythinh/ubfc-phys-s1-s14` (75 GB, labelled MIT), and per-subject uploads `maiyenkhoa11/ubfc-sNN` (about 15 GB each, CC BY-NC-SA 4.0) — Kaggle API search "ubfc"
- MMPD: `jacktangthu/mmpd-rppg` (110 MB, uploaded by the MMPD author, licence "Other", tagged pre-trained model, so probably weights rather than data), `aditianilp/mmpd-dataset-1/2/3` (3.7 + 4.4 + 7.7 GB, labelled MIT) and `anijas0pbq/mmpd-preprocessed-physnet` (2.8 GB) — Kaggle API search "mmpd"
- MCD-derived: `thatdelta/mcd-rppg` (130 GB), and `alekseysavinov/2026-gw-fullhdwebcam-face-crops-ppg-windows-0…6` (about 123 GB in total, Apache 2.0, preprocessed face-crop + PPG windows; "FullHDwebcam" matches an MCD camera name, which is my inference) — Kaggle API search "rppg", "ppg face"
- Small or derivative uploads: `pinggalawardhana/rppgdata` (20 MB, MIT; `DATASET_1/N-gt/vid_small.mp4` + `gtdump.xmp`, the UBFC-1 file layout), `jawadulkarim117/rppg-heart-rate` (CSV features only), `emmanuelolateju/scamps-mini-labels` (labels only) — Kaggle API
- PhysDrive's preprocessed subset is said to be on Kaggle — [PhysDrive-Dataset](https://github.com/WJULYW/PhysDrive-Dataset). My Kaggle searches did not surface its exact slug.

### Inferences
- DLCN is the most valuable new open dataset: large (98 subjects), and it adds night-time and dynamic-light conditions that our mix lacks. It is non-commercial (NC-SA), and the authors ask for an agreement even though the files are publicly downloadable.
- ashfakyeafi/rppg-dataset has phone-like MOV video with an Empatica E4 wrist BVP reference. Wrist BVP lags and is noisier than finger PPG, so check the sync before using it. Its origin and licence are unknown, which makes it risky for publication.

### Gaps
- I could not identify the original source of ashfakyeafi/rppg-dataset; it has no description.
- No Kaggle mirrors were found for PURE, VIPL, COHFACE, iBVP, RLAP or LGI-PPGI.
- I did not find the Kaggle slug for PhysDrive's preprocessed subset.
