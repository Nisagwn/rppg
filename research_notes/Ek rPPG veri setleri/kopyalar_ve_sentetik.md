# Third-party mirrors of rPPG datasets (HF / Kaggle / GitHub / Drive) and synthetic rPPG datasets other than SCAMPS

Method: anonymous HF Hub API queries were run on 2026-10-05 for about 80 search terms: `api/datasets?search=…&limit=100` plus `?blobs=true` per repo to get file lists and sizes. Kaggle searches used the public list endpoint `kaggle.com/api/v1/datasets/list?search=…`, which needs no auth, plus `/datasets/list/{ref}` for file lists. GitHub was searched through `api.github.com/search/repositories`. arXiv and web search were used for synthetic data. Nothing was downloaded and no access was requested. Gating labels are the HF `gated` field: False = open, "auto" = click-through auto-approve, "manual" = owner approves each request.
Caveat: HF `siblings` lists stop at 100,000 files, so the sizes shown for WeiQian98/PURE and Bgeorge/RPPG are lower bounds. The Kaggle file-list endpoint pages at 20 or 200 per request and listed only 3,000 files for thatdelta/mcd-rppg.

## (a) Mirrors and copies of face-video rPPG data with PPG ground truth that can be downloaded now

### Takeaway
Some sources can be downloaded right now with no approval. With raw video plus PPG: UBFC-rPPG (several HF and Kaggle copies), PURE (Thinhnb29/PURE, 41 GB of zips), UBFC-Phys (Kaggle, split per subject), MCD-rPPG (many HF copies plus Kaggle), DLCN (Kaggle) and a PhysDrive subset (Kaggle). MMPD is available only as partial Kaggle splits. Preprocessed crops of UBFC and MCD also exist.
Not open: VIPL-HR, COHFACE, BUAA-MIHR, MR-NIRP-Car, full MMPD, PURE (as frames) and PhysDrive exist only as **manual-gated** WeiQian98 mirrors. VitalVideos repos on HF are cards only, with no files.
No open mirror was found for: MAHNOB-HCI, OBF, LGI-PPGI, iBVP, SUMS, RLAP, ECG-Fitness, MMSE-HR, BP4D+, V4V, VIPL-HR, COHFACE or SCAMPS-derivatives.

### Cited Findings

**Hugging Face: open (gated=False) raw video + PPG**
- `thachha901/UBFC` is UBFC-rPPG DATASET_2, 42 subjects (`UBFC/subjectN/vid.avi` + `ground_truth.txt`). Open, 85 files, 75.03 GB, no license field, uploaded 2025-04-03. It is an unofficial redistribution. — [HF API](https://huggingface.co/api/datasets/thachha901/UBFC?blobs=true)
- `Thinhnb29/PURE` holds the full PURE as 60 per-sequence zips (`PURE/01-01.zip` … each about 0.7–0.8 GB). Open, 41.02 GB, no license, created 2025-03-06. Unofficial. — [HF API](https://huggingface.co/api/datasets/Thinhnb29/PURE?blobs=true)
- MCD-rPPG copies. All have the same 13,204 files and 135.18 GB (3,600 AVI, PPG `.PW`, ECG JSON, `db.csv`) and a cc-by-4.0 card copied from the original:
  - `akramic/mcd_rppg` (open, 3,868 downloads)
  - `wengziheng/mcd_rppg` (gated **auto**)
  - Search also listed these copies: nayana1r, 13110792903qq, milai-oks-sakura (auto), Addy20252027, RampUpAIMLVra, balasubrahmanya, dypknu, Vishal0701, engrarifarshad, luoyongkai, Uday3114, Bgeorge, surui7-7, zoubbi-IP and Shubh782004 (`/mcd_rppg`).
  - The original `kyegorov/mcd_rppg` returned "Invalid username or password" to the anonymous API on 2026-10-05, so it may be private or removed now. The mirrors are the practical source. — [HF API akramic](https://huggingface.co/api/datasets/akramic/mcd_rppg?blobs=true), [HF search rppg](https://huggingface.co/api/datasets?search=rppg&limit=100), [Bgeorge card citing original](https://huggingface.co/datasets/Bgeorge/RPPG/resolve/main/README.md)
- `jjuik2014/UBFC-Phys-all` is gated **auto**, 874.5 GB. It contains `UBFC_Phys_part1..8.zip` (about 29–35 GB each) plus `s17.zip`…`s56.zip` (about 14–16 GB each), and also bundles the unrelated MAFW emotion dataset. No license. Unofficial. — [HF API](https://huggingface.co/api/datasets/jjuik2014/UBFC-Phys-all?blobs=true)

**Hugging Face: open, preprocessed or derived (not raw video)**
- `Horusprg/UBFC-rPPG-Faces` has one 312 MB zip of face clips plus `metadata.csv` (clip_filename, subject_id, one ppg_signal value per clip, so it looks like per-frame clips with a PPG sample). Open, no license, 2026-01-13. — [metadata.csv](https://huggingface.co/datasets/Horusprg/UBFC-rPPG-Faces/resolve/main/metadata.csv)
- `Bgeorge/RPPG` is MCD-rPPG preprocessed with MediaPipe: `faces/slice1-4` (npy face crops, about 823 GB or more), `landmarks/`, `roi/` (8-ROI signals), `MCG_RPPG/preprocessing/*.npz` (127.7 GB) and 2 ResNet3D checkpoints. Open, labelled cc-by-nc-sa-2.0, at least 1,078 GB (listing capped at 100k files). — [HF API](https://huggingface.co/api/datasets/Bgeorge/RPPG?blobs=true), [README](https://huggingface.co/datasets/Bgeorge/RPPG/resolve/main/README.md)
- `acroitoru/rppg_correct` stores rPPG features only: Arrow, with columns `rPPG` (float16 nested lists), frame indices, fps, video_path and identity. It has 164,708 rows, 27.4 GB, open, no license. The source videos are unclear; the owner's other repos are deepfake/MAVOS work. — [dataset_info.json](https://huggingface.co/datasets/acroitoru/rppg_correct/resolve/main/dataset_info.json)
- `huzz7/ubfcpart_288245_stmap_0310` has 9,405 STMap PNGs from part of UBFC, 0.52 GB, apache-2.0 on the card, no documentation. — [HF API](https://huggingface.co/api/datasets/huzz7/ubfcpart_288245_stmap_0310?blobs=true)
- `capruxel/thenar-rppg-hr-2026` contains only derived ROI time series from one thenar/hand RGB+NIR session. It is not face video. cc-by-nc-4.0. — [README](https://huggingface.co/datasets/capruxel/thenar-rppg-hr-2026/resolve/main/README.md)
- `NetherlandsForensicInstitute/rppg-deepfake-detection` has 500 MP4s, 1.88 GB, sorted into real and fake (Sora, AkoolAI and others), with annotations for gender, skin colour, head movement and lighting. It has **no PPG ground truth**, so it is not usable for supervised rPPG. — [annotations.json](https://huggingface.co/datasets/NetherlandsForensicInstitute/rppg-deepfake-detection/resolve/main/annotations.json)

**Hugging Face: gated manual (owner WeiQian98; no README, no license field; created June to Sept 2026)**
- `WeiQian98/UBFC-rPPG`: 75.03 GB, includes the original `Agreement.xlsx`.
- `WeiQian98/MMPD`: 371.87 GB, 659 `.mat`.
- `WeiQian98/mini_MMPD`: 50.78 GB. A duplicate is `leefangbiao/mini_MMPD` (manual, 2026-09-30).
- `WeiQian98/VIPL-HR`: 51.39 GB, 3,130 AVI + `wave.csv`/`gt_HR.csv`/`gt_SpO2.csv`, includes ReadMe.pdf.
- `WeiQian98/COHFACE`: 0.58 GB, 164 AVI + hdf5.
- `WeiQian98/BUAA-MIHR`: 237.19 GB.
- `WeiQian98/MR-NIRP-Car`: 30.93 GB, 185 AVI + BVP CSV.
- `WeiQian98/PURE`: at least 33.2 GB as frames (listing capped).
- `WeiQian98/PhysDrive`: 74.4 GB.
- `WeiQian98/DLCN`: 47.4 GB.
- The owner approves each request. These are unofficial re-uploads of license-restricted datasets. — [HF API author listing](https://huggingface.co/api/datasets?author=WeiQian98&limit=100), [VIPL-HR files](https://huggingface.co/api/datasets/WeiQian98/VIPL-HR?blobs=true)
- `zodi1121/UBF_clean` is manual-gated and contains only a `.venv` and code (about 1 GB), not data. — [HF API](https://huggingface.co/api/datasets/zodi1121/UBF_clean?blobs=true)

**Hugging Face: cards only, no data files**
- `pjtoye/VitalVideos-Europe-1`, `-Africa-1` and `-Worldwide` each hold only README.md. The cards say the data is "not publicly downloadable… granted under academic or commercial license upon request". Worldwide has about 6,500 participants, 60 fps, Basler + iPhone 15 Pro, PPG at 60 Hz and 500 Hz, ECG, BP and SpO2. — [README](https://huggingface.co/datasets/pjtoye/VitalVideos-Worldwide/resolve/main/README.md)
- `xilin-x/BUAA-MIHR` is the official card (cc-by-nc-sa-4.0) with a release-agreement PDF. Access is by e-mail from an institutional address only; Gmail is rejected. It has 15 subjects, 165 videos, 640×480 at 30 fps, CMS50E PPG. — [README](https://huggingface.co/datasets/xilin-x/BUAA-MIHR/resolve/main/README.md)
- `1Li/DLCN-rPPG` has a README only (31 bytes). `phdsangdiago/MMPD_27_33` is empty. `HY2333/MMPD_Bench` is an unrelated polarimetry dataset (name collision). — [HF API](https://huggingface.co/api/datasets/HY2333/MMPD_Bench?blobs=true)

**Kaggle (all public, no gating beyond a Kaggle login for download; licenses are uploader-declared)**
- UBFC-rPPG DATASET_2:
  - `malekdinarito/ubfc-rppg-dataset`: 33.53 GB, "CC0" as declared by the uploader, 4,393 downloads.
  - `hiyorindm/ubfc-rppg-2`: 33.53 GB.
  - `ashfakyeafi/ubfc-2`: 12.95 GB, a partial copy (subject10+…). — [Kaggle API search "ubfc"](https://www.kaggle.com/api/v1/datasets/list?search=ubfc)
- UBFC-Phys (vid_sN_T1-3.avi + bvp/eda CSV):
  - `hcmuehmduck/ubfc-phys`: 212.55 GB, s43–s56.
  - `phanquythinh/ubfc-phys-s1-s14`: 75.03 GB.
  - `jemmpn/ubfc-2-15-28`: 32.84 GB, s15–16.
  - `diulinhpn/ubfc-17-23`: 104.59 GB.
  - `diulinhpn/ubfc-24-28`: 72.43 GB.
  - `maiyenkhoa11/ubfc-s6`…`ubfc-s42`: one subject per dataset, about 14–18 GB each, CC BY-NC-SA 4.0.
  - Together these appear to cover most of the 56 subjects. — [Kaggle API search "ubfc-phys"](https://www.kaggle.com/api/v1/datasets/list?search=ubfc-phys)
- `thatdelta/mcd-rppg` is MCD-rPPG, 130.03 GB, uploaded 2026-06-18, 6 downloads. The file listing shows the metadata folder (ecg JSON, meta txt, db.csv); the rest is presumably video. — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=mcd-rppg)
- `alekseysavinov/2026-gw-fullhdwebcam-face-crops-ppg-windows-0..6` is MCD-rPPG FullHD-webcam face crops already cut into PPG windows (`preprocessed_windows/db.csv`, `ppg/*.PW`). 7 parts of about 12.7–19 GB each, about 124 GB total, Apache 2.0 as declared by the uploader. — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=ppg%20video)
- `dalaoplan/rppg-dlcn` is DLCN ("rPPG dataset under dynamic lighting conditions at night"), `DLCN/P*_*.h5`, 42.77 GB, CC BY-NC-SA 4.0. — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=rppg)
- PhysDrive on Kaggle:
  - `xiaoyang274/physdrive` (16.48 GB, CC BY-NC-SA 4.0, 7,201 downloads) appears official, from an author account. It has RGB.mp4 and IR.mp4 + BVP/ECG/HR/RESP/SPO2 .mat. Its files are labelled "one subject sample".
  - `xiaoyang274/physdriveone-subject-sample` (1.04 GB).
  - `goldfish9901/physdrive-rda-exports` (7.61 GB). — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=physdrive)
- MMPD partial:
  - `aditianilp/mmpd-dataset-1/2/3` (3.74, 4.42 and 7.74 GB of `pN_0.mat`, MIT declared, unofficial).
  - `anijas0pbq/mmpd-preprocessed-physnet` (2.84 GB of rPPG-Toolbox npy).
  - `jacktangthu/mmpd-rppg` (0.1 GB) is only the official agreement PDFs and GIFs, no data. — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=mmpd)
- `ashfakyeafi/rppg-dataset` (4.37 GB) has 7 subjects with `video.MOV` + Empatica E4 BVP/HR/IBI/EDA. Its provenance is undocumented. — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=rppg)
- Other rppg hits on Kaggle are small caches or features, not raw data: `naziasultana0715/mmse-hr-dataset` (actually the "Benefit_of_Distraction" code repo, not MMSE-HR), `hoangnam729/obf-psychiatric-dataset` (actigraphy, not the Oulu OBF), `emmanuelolateju/scamps-mini-labels` (10 CSVs), `jawadulkarim117/rppg-heart-rate` (features), `thinhphan272/ffpp-c23-rppg-cache` (FF++ deepfake frames). — [Kaggle API](https://www.kaggle.com/api/v1/datasets/list?search=rppg)

**GitHub**
- Repo search for "rppg dataset" returns mostly official dataset pages that point to request forms: McJackTang/MMPD_rPPG_dataset, PhysiologicAILab/iBVP-Dataset, KegangWangCCNU/RLAP-dataset, xilin-x/Large-scale-Multi-illumination-HR-Database, yangze68/BH-rPPG-dataset, jdh-algo/MHAD-Dataset, McJackTang/FusionVitals, Health-HCI-Group/F3Mamba (dual-view smartphone PPG dataset), alialnaji/CLBP-300-Dataset and marukosan93/ORPDAD. No repo was found that hosts video+PPG in GitHub Releases. — [GitHub search](https://api.github.com/search/repositories?q=rppg+dataset&sort=stars&per_page=30)

### Inferences
- Copies with the least friction for adding training data: Thinhnb29/PURE (open, 41 GB), the UBFC-Phys Kaggle splits, the MCD-rPPG HF mirrors, DLCN on Kaggle and PhysDrive on Kaggle. Phone-camera data inside these comes from MCD-rPPG (mobile camera view) and the partial MMPD Kaggle splits.
- The WeiQian98 mirrors (VIPL-HR, COHFACE, MMPD, BUAA-MIHR, MR-NIRP-Car) only help if the owner approves. They are unofficial; using them still requires the original license (most are research-only and ban redistribution).
- Almost all non-MCD mirrors redistribute data whose original licenses forbid redistribution: UBFC, PURE, MMPD, VIPL-HR and COHFACE. The "CC0" or "MIT" labels on Kaggle are uploader claims and do not override the original terms.

### Gaps
- Exact contents of `thatdelta/mcd-rppg` beyond the first 3,000 listed files were not verified.
- Full file counts for `Bgeorge/RPPG` and `WeiQian98/PURE` are unknown because the listing is capped at 100k.
- Whether the WeiQian98 owner actually approves requests is unknown; nothing was requested.
- Cloud drives (Baidu or Google Drive links in papers) cannot be searched systematically. Only the UCLA-VMG Drive link was found (see below).
- It was not checked whether PhysDrive `xiaoyang274/physdrive` (16.5 GB) holds more than one subject. The file prefix says "one subject sample", but its size is about 16× the separate sample dataset.

## (b) Synthetic rPPG datasets other than SCAMPS usable for pretraining

### Takeaway
No new large synthetic rPPG **dataset** with open downloads was found for 2024–2026. Apart from SCAMPS, the options are generators:
- **UCLA-VMG rppg_synthetic**: code plus a Google Drive with weights and samples; synthetic videos are made with DECA and BIDMC PPG.
- **MA-rPPG Video Toolbox**: motion-augments UBFC, PURE or SCAMPS yourself; driving videos are on Drive.
- Recent papers (Ou et al. 2023 noise-augmented SCAMPS; Heartian, Sept 2026) report no released data.

### Cited Findings
- UCLA-VMG/rppg_synthetic (code for "Synthetic generation of face videos with plethysmograph physiology", CVPR 2022, Wang et al.). The repo contains `rppg_generation.ipynb`, `prn_training.ipynb` and `train_biofacenet.ipynb`. It builds videos from the BUPT-Balanced face images + BIDMC PPG through DECA. Pretrained BioFaceNet weights and "some samples of real data" are on Google Drive (drive.google.com/drive/folders/1WJGFVUfi7HvoFAuUV4J_VwxW2GwU_SUw). No prebuilt synthetic video set is offered; the user has to generate it. A fork with sample results exists at JunyoungChoi92/rppg_synthetic. — [GitHub API contents](https://api.github.com/repos/UCLA-VMG/rppg_synthetic/contents), [README](https://raw.githubusercontent.com/UCLA-VMG/rppg_synthetic/main/readme.md), [patent "Synthetic generation of face videos with plethysmograph physiology"](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12539047)
- MA-rPPG Video Toolbox (Paruchuri et al., "Motion Matters", WACV 2024 Oral) adds motion transfer (face-vid2vid) to UBFC-rPPG, PURE or SCAMPS and copies the ground truth over. Output is about 5 GB per augmented UBFC video as npy. Augmenting all 42 UBFC videos took about 22 h on 4×A4500. The TalkingHead-1KH driving videos are on Google Drive. The README provides no prebuilt augmented datasets. rPPG-Toolbox supports them via `DATA_AUG: Motion`. — [MA-rPPG README](https://github.com/yahskapar/MA-rPPG-Video-Toolbox), [rPPG-Toolbox README](https://github.com/ubicomplab/rPPG-Toolbox), [arXiv 2303.12059](https://arxiv.org/pdf/2303.12059)
- Ou, Zhang, Wang, Patel, McDuff, Yang, Liu, "Training Robust Deep Physiological Measurement Models with Synthetic Video-based Data" (arXiv 2311.05371). It adds real-world noise to SCAMPS videos and signals and reports average MAE dropping from 6.9 to 2.0 on three real datasets. No data or code link appears on the abstract page. — [arXiv](https://arxiv.org/abs/2311.05371)
- Heartian (Fan, Echevarria, Paruchuri, Akşit; SIGGRAPH Asia 2026 TC, submitted 2026-09-22) is a physiology-aware relightable Gaussian head avatar that encodes rPPG through per-frame albedo modulation and is evaluated on rendered MMPD avatars. No dataset or code URL is on the arXiv page. — [arXiv abs](https://arxiv.org/abs/2609.28539)
- Earlier Microsoft avatar synthetics: McDuff et al. "Advancing Non-Contact Vital Sign Measurement using Synthetic Avatars" (arXiv 2010.12949) and "Synthetic Data for Multi-Parameter Camera-Based Physiological Sensing" (arXiv 2110.04902). These were precursors to SCAMPS; the only public release is SCAMPS itself. — [arXiv 2010.12949](https://arxiv.org/pdf/2010.12949), [arXiv 2110.04902](https://arxiv.org/pdf/2110.04902)
- PhysFlow (arXiv 2407.21519) does skin-tone transfer augmentation for rPPG with conditional normalizing flows. It is a method, and no dataset was found. — [arXiv](https://arxiv.org/pdf/2407.21519)
- rePPG ("Relighting Photoplethysmography Signal to Video", Biomimetics 11(4), 2026) is a generative method aimed in part at synthetic data generation. No dataset release was confirmed. — [MDPI](https://www.mdpi.com/2313-7673/11/4/230)
- On HF, searches for scamps, synthppg, synthetic-rppg, rppg-synthetic and avatar-physiology returned **no** datasets. On Kaggle the only SCAMPS item is `emmanuelolateju/scamps-mini-labels` (10 label CSVs). — [HF search scamps](https://huggingface.co/api/datasets?search=scamps&limit=50), [Kaggle search](https://www.kaggle.com/api/v1/datasets/list?search=scamps)

### Inferences
- For synthetic pretraining beyond SCAMPS, the realistic route is to generate data locally:
  - Motion-augment the UBFC/PURE/MCD data you already have with MA-rPPG (expensive in GPU hours and disk).
  - Or run the UCLA DECA-based generator with public PPG (BIDMC, or MCD PPG).
- Deepfake-related HF and Kaggle sets (NFI rppg-deepfake-detection, FF++ caches) have no PPG labels and are useless for supervised pretraining.

### Gaps
- An arXiv API query for synthetic+rPPG returned no parseable results, so other 2025–2026 synthetic-data papers may have been missed. No release was found for names like "SynthPPG", "PhysGen" or "UCLA-synthetics" as standalone datasets.
- The Lacuna-indexed Microsoft multi-parameter synthetics and the "1,000 avatars driven by PhysioNet PPG" pipeline mentioned in search snippets had no confirmed public download.
- The contents and size of the UCLA Drive folder were not inspected.
