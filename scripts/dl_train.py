#!/usr/bin/env python
"""
FactorizePhys (rPPG-Toolbox, NeurIPS 2024) ince ayarı: PURE ön-eğitimli ağırlıklardan başlayıp
MCD-rPPG (3 kamera, dinlenme + egzersiz) ve UBFC-rPPG'nin test DIŞI kişileriyle eğitir.

* Veri: scripts/dl_prepare.py çıktıları (data/dl/mcd, data/dl/ubfc). Kişi bazında ayrım:
  kişilerin ~%10'u doğrulama, geri kalanı eğitim. Test kişileri zaten hiç işlenmemiştir.
* Her epoch: videolardan rastgele başlangıçlı 160 karelik parçalar (uzunlukla orantılı örnekleme).
* Artırma: yatay çevirme, hız değişimi (0.8–1.25x; HR dağılımını genişletir), parlaklık ölçeği.
* Kayıp: örnek başına negatif Pearson. MCD etiketi ters çevrilir (bkz. ChunkSampler).
* --arch mmrphys: MMRPhys (Joshi ve Cho 2025) rastgele başlatmayla (sıfırdan). Makaledeki gibi SmoothL1 kaybı
  (standartlaştırılmış tahmin ve etiket); TSFM eğitimde etiketi kullanır. --scratch: FactorizePhys de sıfırdan.
* Seçim: doğrulama videolarında pencere MAE (argmax, 10 s) en düşük epoch -> best.pth
* Dayanıklılık: her epoch sonunda last.pth (model + optimizer + zamanlayıcı); tekrar çalıştırınca devam eder.
  --deadline "2026-09-28 04:15" verilirse o saatte güvenle durur.

    python scripts/dl_train.py --epochs 30 --steps 600 --deadline "2026-09-28 04:15"
    python scripts/dl_train.py --arch mmrphys --epochs 200 --lr 1e-3

İsteğe bağlı iyileştirmeler (hepsi varsayılan olarak kapalı; kapalıyken davranış öncekiyle aynı):
  --spec-loss 0.2     frekans alanı kaybı (spectral_kl): yanlış frekansa/harmoniğe kilitlenmeyi cezalandırır
  --ema 0.999         ağırlık ortalaması; doğrulama ve best.pth bununla (tek şanslı epoch'a bağlı seçimi azaltır)
  --val-viterbi       en iyi epoch'u raporlanan yöntemle (Viterbi) seç
  --amp               float16 karışık hassasiyet (CUDA), T4'te daha hızlı
  --speed 0.7 1.5     daha geniş hız artırması (yüksek nabız örnekleri)
  --hr-balance 3      seyrek nabız aralıklarındaki videoları en fazla 3 kat sık örnekle
"""
import argparse
import glob
import json
import os
import time
import zlib
from datetime import datetime

import numpy as np

from dl_common import (ARCHS, CHUNK, MODEL_SYNC, PER_VIDEO_SYNC, PRETRAINED, build_model, hr_from_bvp,
                       label_shift, predict_video, reference_hr, shift_label, video_decision)
from dl_quality import compute as quality


CLEAN = True  # --no-clean ile kapatılır (karşılaştırma için)
_VCACHE = {}  # yol -> (mtime, kayıt | None): her epoch'ta binlerce dosyayı yeniden taramamak için


def _video_entry(p, min_face):
    m = np.load(p)
    if float(m["face_rate"]) < min_face or int(m["n"]) < CHUNK * 2:
        return None
    b = m["bvp"]  # bozuk referans: NaN ya da düz (sensör kayıt almamış, ör. MCD 4952) -> kayıp patlar
    if not np.all(np.isfinite(b)) or (np.lib.stride_tricks.sliding_window_view(b, CHUNK)[::40].std(1) < 1e-6).mean() > 0.2:
        return None
    source, camera = str(m["source"]), str(m["camera"])
    q = quality(p) if CLEAN else None  # etiket kalitesi (dl_quality.py); yoksa burada hesaplanıp .kal yazılır
    snk = load_sync(p) if source in MODEL_SYNC else None
    if q is not None and not video_decision(q, source, camera, snk):
        return None
    return {"npz": p, "npy": p[:-4] + ".npy", "n": int(m["n"]), "person": str(m["person"]),
            "source": source, "camera": camera, "q": q, "snk": snk,
            "hr": video_hr(b, p[:-4] + ".kal"),
            "vote": float(m["polarity"]) * float(m["polarity_corr"]) if "polarity" in m.files else 0.0}


def load_sync(npz):
    """dl_sync_check.py --write çıktısı (model tabanlı hizalama); yoksa None."""
    p = npz[:-4] + ".snk"
    return {k: v.item() for k, v in np.load(p).items()} if os.path.exists(p) else None


def video_hr(bvp, kal=None, fs=30.0):
    """Videonun tipik nabzı (BPM): etiket kalitesi dosyası (.kal, dl_quality) varsa iyi pencerelerin medyanı, yoksa
    tüm etiketin spektral tepesi. --hr-balance örneklemesinde ve günlükteki nabız dağılımında kullanılır."""
    if kal and os.path.exists(kal):
        with np.load(kal) as k:
            if "win_ok" in k.files and k["win_ok"].any():
                return float(np.median(k["hr_l"][k["win_ok"]]))
    from rppg.filtering import preprocess_bvp
    from rppg.hr import hr_fft
    return float(hr_fft(preprocess_bvp(np.asarray(bvp, dtype=float), fs), fs))


HR_BIN = 10.0  # BPM


def hr_balance_weights(hrs, max_boost=4.0):
    """Video başına çarpan: nabız histogramında (10 BPM kutular) seyrek kutudaki videolar daha sık örneklenir.
    Çarpan = (en kalabalık kutu / kendi kutusu), max_boost ile sınırlı; aşırı seyrek (tek videoluk) kutuların
    birkaç videoyu ezberletmesini önler."""
    hrs = np.asarray(hrs, dtype=float)
    bins = np.floor(hrs / HR_BIN).astype(int)
    _, inv, cnt = np.unique(bins, return_inverse=True, return_counts=True)
    return np.minimum(cnt.max() / cnt[inv], max_boost)


TRAIN_SOURCES = ("mcd", "ubfc", "pure", "ubfcphys", "mpu", "mmpd", "vipl", "cohface", "dlcn")  # test_* klasörleri hiç okunmaz


def list_videos(root, min_face=0.5):
    vids = []
    for p in sorted(p for sub in TRAIN_SOURCES
                    for p in glob.glob(os.path.join(root, sub, "*.npz"))):
        snk = p[:-4] + ".snk"  # hizalama eğitim başladıktan sonra yazılabilir: değişince video yeniden okunur
        mt = (os.path.getmtime(p), os.path.getmtime(snk) if os.path.exists(snk) else 0.0)
        if p not in _VCACHE or _VCACHE[p][0] != mt:
            try:
                entry = _video_entry(p, min_face)
            except Exception as e:  # noqa: BLE001  yeni veri setinden bozuk/beklenmedik dosya eğitimi düşürmesin
                print(f"  atlandı {os.path.basename(p)}: {e!r}", flush=True)
                entry = None
            _VCACHE[p] = (mt, entry)
        if _VCACHE[p][1] is not None:
            vids.append(_VCACHE[p][1])
    # Etiket işareti (modelin kuralına göre çarpan). MCD: ters (elle bulundu). İşaret oyu kaydedilmiş veri setleri
    # (UBFC-Phys): aynı sensör -> tek karar, videoların korelasyonla ağırlıklı oyu (bkz. dl_prepare.label_polarity).
    votes = {}
    for v in vids:
        votes[v["source"]] = votes.get(v["source"], 0.0) + v["vote"]
    for v in vids:
        v["mult"] = -1.0 if v["source"] == "mcd" else (-1.0 if votes.get(v["source"], 0.0) < 0 else 1.0)
        v["shift"] = label_shift(v["q"], v["source"], v["camera"], v["snk"]) if CLEAN else 0
        if CLEAN and (v["source"] in PER_VIDEO_SYNC or v["source"] in MODEL_SYNC):
            v["mult"] = 1.0  # işaret yerine hizalama: tepe korelasyonu pozitif olacak şekilde kaydırıldı
    return vids


SPEED = (0.8, 1.25)  # hız artırma aralığı (--speed); >1 nabzı hızlandırır
MAX_SPAN = int(np.ceil(CHUNK * SPEED[1])) + 1  # en hızlı artırmada gereken kare sayısı


def is_val(person):
    return zlib.crc32(person.encode()) % 10 == 0


def pick_val(vids, n, prev=()):
    """Doğrulama videoları: doğrulama kişilerinden veri seti/kamera başına eşit pay, her birinde eşit aralıklı.
    Kamera ayrı grup: 7. tur D'de MCD'nin 3 kamerası tek grupta 6 videoyla temsil ediliyordu; telefon/USB
    testindeki kötüleşme en iyi epoch seçiminde görülmedi.
    6. turda doğrulama ilk gelen MCD/UBFC videolarından seçilmişti; yeni verinin etkisi görülemiyordu.
    prev: önceki seçim; hâlâ geçerli olanlar korunur, yalnızca boş kalan pay doldurulur (7. tur B: küme her epoch
    değişince aynı en iyi model 1.4-4.3 BPM arasında ölçülüyordu, en iyi epoch seçimi gürültülüydü)."""
    prev = set(prev)
    groups = {}
    for v in vids:
        if is_val(v["person"]):
            groups.setdefault((v["source"], v.get("camera", "")), []).append(v)
    k = max(1, n // max(1, len(groups)))
    out = []
    for g in sorted(groups):
        vs = groups[g]
        keep = [v for v in vs if v["npz"] in prev][:k]
        rest = [v for v in vs if v["npz"] not in prev]
        need = min(k - len(keep), len(rest))
        out += keep + ([rest[i] for i in np.linspace(0, len(rest) - 1, need).astype(int)] if need > 0 else [])
    return out


SOURCE_WEIGHTS = {}  # --source-weights: veri setinin eğitim parçalarındaki payı (boşsa kare sayısıyla orantılı)


def source_shares(vids, weights):
    """Veri seti başına örnekleme payı. weights boşsa kare sayısıyla orantılı (1-6. tur, 7. tur B/D);
    verilmişse yalnızca eldeki veri setleri arasında normalleştirilir, listede olmayanın payı 0."""
    frames = {}
    for v in vids:
        frames[v["source"]] = frames.get(v["source"], 0) + v["n"]
    raw = {s: (weights.get(s, 0.0) if weights else f) for s, f in frames.items()}
    tot = sum(raw.values()) or 1.0
    return {s: r / tot for s, r in raw.items()}, frames


HR_BALANCE = 0.0  # --hr-balance: en fazla kaç kat (0: kapalı, örnekleme yalnızca uzunlukla orantılı)


class ChunkSampler:
    def __init__(self, vids):
        self.vids = vids
        shares, frames = source_shares(vids, SOURCE_WEIGHTS)
        # veri seti içinde kare sayısıyla orantılı; veri setleri arasında shares (7. tur D: MCD 30 s'ye inip DLCN ve
        # COHFACE eklenince MCD'nin kare payı ~%78'den ~%62'ye düştü, MCD tabanlı testler kötüleşti)
        w = np.array([shares[v["source"]] * v["n"] / frames[v["source"]] for v in vids], dtype=float)
        if HR_BALANCE > 1:
            w = w * hr_balance_weights([v["hr"] for v in vids], HR_BALANCE)
        self.p = w / w.sum()
        self.cache = {}
        print("  örnekleme payı: " + ", ".join(f"{s} %{100 * x:.0f}" for s, x in sorted(shares.items(), key=lambda t: -t[1])),
              flush=True)

    def _frames(self, v):
        item = self.cache.get(v["npy"])
        if item is None:  # iş parçacıkları arasında güvenli: çift tek seferde yazılır
            bvp = np.load(v["npz"])["bvp"]
            # MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli modelle korelasyon ~ -0.75, gecikme ~0);
            # diğer veri setleri için çarpan list_videos'ta belirlenir
            kal = v["npz"][:-4] + ".kal"
            ok = np.load(kal)["frame_ok"] if CLEAN and os.path.exists(kal) else np.ones(len(bvp), bool)
            bvp = shift_label(bvp, v.get("shift", 0))  # etiket-video zaman hizası (dl_common.CAMERA_SHIFT)
            item = (v.get("mult", 1.0) * bvp, ok)
            self.cache[v["npy"]] = item
        # Kareler her çağrıda yeniden eşlenir (mmap) ve parça kopyalanınca bırakılır: binlerce videonun eşlemesini
        # açık tutmak saatler içinde süreç belleğinde birikiyordu (6. tur ~3 saatte durdu); yalnızca etiketler önbellekte
        return (np.load(v["npy"], mmap_mode="r"),) + item

    def sample(self, rng):
        for _ in range(20):  # etiketi düz/bozuk parçayı reddet
            clip, lab, prm = self._sample(rng)
            if np.isfinite(lab).all() and np.abs(lab).max() < 50:
                return clip, lab, prm
        return clip, lab, prm

    def _sample(self, rng):
        """CPU'da yalnızca ham uint8 kareler kopyalanır; hız/çevirme/parlaklık GPU'da (gpu_augment) uygulanır."""
        v = self.vids[rng.choice(len(self.vids), p=self.p)]
        frames, bvp, ok = self._frames(v)
        speed = rng.uniform(*SPEED) if rng.random() < 0.5 else 1.0
        span = min(int(np.ceil(CHUNK * speed)) + 1, len(frames))
        s = rng.integers(0, len(frames) - MAX_SPAN + 1) if len(frames) >= MAX_SPAN else 0
        s = min(s, len(frames) - span)
        clip = np.zeros((MAX_SPAN,) + frames.shape[1:], dtype=np.uint8)
        n = min(MAX_SPAN, len(frames) - s)
        clip[:n] = frames[s:s + n]
        lab = np.asarray(bvp[s:s + span], dtype=np.float32)
        pos = np.minimum(np.arange(CHUNK) * speed, span - 1.001)
        lab = np.interp(pos, np.arange(len(lab)), lab)  # zaman ekseninde yeniden örnekle -> nabız speed katı
        prm = np.array([speed, span, rng.random() < 0.5, rng.uniform(0.8, 1.2)], dtype=np.float32)
        sd = lab.std()
        if sd < 1e-6 or ok[s:s + span].mean() < 0.8:  # etiketin kötü olduğu bölüm (sensör kayması vb.)
            return clip, np.full(CHUNK, np.nan, dtype=np.float32), prm
        return clip, ((lab - lab.mean()) / sd).astype(np.float32), prm

    def batch(self, bs, seed):
        rng = np.random.default_rng(seed)  # iş parçacığı başına ayrı üreteç
        xs, ys, ps = zip(*(self.sample(rng) for _ in range(bs)))
        return np.stack(xs), np.stack(ys), np.stack(ps)


def gpu_augment(clips_u8, prm, device):
    """[B,MAX_SPAN,72,72,3] uint8 + [B,4] (hız, gerçek uzunluk, çevir, parlaklık) -> [B,3,CHUNK+1,72,72] float.
    Toolbox gibi son kare tekrarlanır (model içinde diff alınır)."""
    import torch
    x = torch.as_tensor(clips_u8, device=device).float()
    prm = torch.as_tensor(prm, device=device)
    t = torch.arange(CHUNK, device=device, dtype=torch.float32)
    out = []
    for i in range(x.shape[0]):
        pos = torch.clamp(t * prm[i, 0], max=prm[i, 1] - 1.001)
        j = pos.long()
        w = (pos - j)[:, None, None, None]
        c = x[i, j] * (1 - w) + x[i, j + 1] * w
        if prm[i, 2] > 0.5:
            c = torch.flip(c, dims=[2])
        c = torch.clamp(c * prm[i, 3], 0, 255)
        if BOX_JITTER > 0:
            c = box_jitter(c, BOX_JITTER)
        if PHONE_AUG and torch.rand(()) < 0.6:
            c = phone_degrade(c)
        out.append(c)
    x = torch.stack(out).permute(0, 4, 1, 2, 3)
    return torch.cat([x, x[:, :, -1:]], dim=2)


PHONE_AUG = False  # --phone-aug
BOX_JITTER = 0.0  # --box-jitter


def box_jitter(c, j):
    """Yüz kutusu farkı (parça boyunca sabit): kırpıntı ±j oranında ölçeklenir ve kaydırılır, [T,72,72,3] 0-255.
    Eğitim kırpıntıları Haar kutusundan, uygulamanınki pico/YuNet kutusundan (YuNet -> pico eşlemesinde bile merkez
    ~%3, boyut %94-107); model belirli bir kutu yerleşimine alışmasın. Dışarı taşan kenar en yakın pikselle dolar."""
    import torch
    import torch.nn.functional as F
    dev = c.device
    x = c.permute(0, 3, 1, 2)
    k = 1 + (torch.rand((), device=dev) * 2 - 1) * j       # >1: kutu büyük (yüz küçük görünür)
    d = (torch.rand(2, device=dev) * 2 - 1) * j            # kutu boyutunun oranı olarak kayma
    theta = torch.zeros(x.shape[0], 2, 3, device=dev)
    theta[:, 0, 0] = theta[:, 1, 1] = k
    theta[:, :, 2] = d * 2
    grid = F.affine_grid(theta, list(x.shape), align_corners=False)
    x = F.grid_sample(x, grid, mode="bilinear", padding_mode="border", align_corners=False)
    return x.permute(0, 2, 3, 1)


def phone_degrade(c):
    """Telefon kamerası benzeri bozulmalar, [T,72,72,3] float 0-255 (her biri ayrı olasılıkla):
    el titremesi (yumuşak rastgele yürüyüş, ±4 px), düşük çözünürlük / sıkıştırma bulanıklığı (24-56 px'e küçültüp
    geri büyütme), renk sıcaklığı (kanal kazancı ±%15), loş ışık (kazanç 0.35-1) + sensör gürültüsü + 8 bit
    nicemleme. Eğitim verisi laboratuvar webcam'i; uygulama telefonda çalışıyor."""
    import torch
    import torch.nn.functional as F
    T = c.shape[0]
    dev = c.device
    x = c.permute(0, 3, 1, 2)  # [T,3,H,W]
    if torch.rand(()) < 0.5:  # el titremesi
        step = torch.randn(T, 2, device=dev) * 0.35
        walk = torch.clamp(torch.cumsum(step, 0) - step.mean(0) * torch.arange(1, T + 1, device=dev)[:, None], -4, 4)
        theta = torch.zeros(T, 2, 3, device=dev)
        theta[:, 0, 0] = theta[:, 1, 1] = 1
        theta[:, :, 2] = walk * (2 / x.shape[-1])
        grid = F.affine_grid(theta, list(x.shape), align_corners=False)
        x = F.grid_sample(x, grid, mode="bilinear", padding_mode="border", align_corners=False)
    if torch.rand(()) < 0.5:  # düşük çözünürlük / sıkıştırma
        size = int(torch.randint(24, 57, ()))
        x = F.interpolate(F.interpolate(x, size=size, mode="area"), size=x.shape[-1], mode="bilinear",
                          align_corners=False)
    if torch.rand(()) < 0.5:  # renk sıcaklığı
        x = x * (0.85 + 0.3 * torch.rand(1, 3, 1, 1, device=dev))
    if torch.rand(()) < 0.5:  # loş ışık + gürültü + nicemleme
        g = 0.35 + 0.65 * torch.rand((), device=dev)
        sigma = 1.0 + 5.0 * torch.rand((), device=dev)
        x = torch.round(torch.clamp(x * g + torch.randn_like(x) * sigma, 0, 255))
    return torch.clamp(x, 0, 255).permute(0, 2, 3, 1)


class Prefetcher:
    """Batch'leri arka plan iş parçacıklarında önden hazırlar (numpy GIL'i bırakır; GPU ile örtüşür)."""
    def __init__(self, sampler, bs, seed, threads=3, depth=6):
        from collections import deque
        from concurrent.futures import ThreadPoolExecutor
        self.sampler, self.bs, self.seed = sampler, bs, seed
        self.ex = ThreadPoolExecutor(threads)
        self.q = deque(self._submit() for _ in range(depth))

    def _submit(self):
        self.seed += 1
        return self.ex.submit(self.sampler.batch, self.bs, self.seed)

    def next(self):
        f = self.q.popleft()
        self.q.append(self._submit())
        return f.result()

    def close(self):
        self.ex.shutdown(wait=False, cancel_futures=True)


def neg_pearson(pred, lab):
    import torch
    p = pred - pred.mean(dim=1, keepdim=True)
    y = lab - lab.mean(dim=1, keepdim=True)
    r = (p * y).sum(1) / (torch.sqrt((p ** 2).sum(1) * (y ** 2).sum(1)) + 1e-8)
    return (1 - r).mean()


def spectral_kl(pred, lab, fs=30.0, band=(0.7, 3.5), nfft=1024):
    """Frekans alanı kaybı: nabız bandındaki normalize güç spektrumları arasında KL(etiket || tahmin).
    Pearson dalga şeklini eşler ama yanlış frekanstaki (ör. harmonik) güçlü bileşeni yeterince cezalandırmaz;
    bu terim doğrudan nabız frekansını hedefler. nfft=1024 sıfır dolgu: 160 karede ~1.8 BPM ızgara."""
    import torch
    win = torch.hann_window(pred.shape[1], device=pred.device, dtype=torch.float32)

    def psd(x):
        x = (x.float() - x.float().mean(1, keepdim=True)) * win
        return torch.fft.rfft(x, n=nfft).abs() ** 2

    f = torch.fft.rfftfreq(nfft, d=1.0 / fs).to(pred.device)
    m = (f >= band[0]) & (f <= band[1])
    p, q = psd(pred)[:, m], psd(lab)[:, m]
    p = p / (p.sum(1, keepdim=True) + 1e-8)
    q = q / (q.sum(1, keepdim=True) + 1e-8)
    return (q * (torch.log(q + 1e-8) - torch.log(p + 1e-8))).sum(1).mean()


def smooth_l1(pred, lab):
    import torch
    p = (pred - pred.mean(dim=1, keepdim=True)) / (pred.std(dim=1, keepdim=True) + 1e-8)
    return torch.nn.functional.smooth_l1_loss(p, lab)  # etiket zaten parça başına standartlaştırılmış


LOSSES = {"pearson": neg_pearson, "smoothl1": smooth_l1}


VAL_GROUPS = {}  # son doğrulamanın kaynak/kamera bazında MAE'si (günlüğe yazılır)


VAL_VITERBI = False  # --val-viterbi: seçim, raporlanan yöntemle (Viterbi) aynı ölçütle yapılır


class EMA:
    """Ağırlıkların üstel hareketli ortalaması (--ema). module: aynı mimaride ayrı bir model (eğitilen modelin kopyası);
    parametreler ve kayan nokta tamponları ortalanır, tam sayı tamponları (ör. sayaçlar) kopyalanır."""

    def __init__(self, module, decay):
        self.module, self.decay = module, decay

    def update_parameters(self, model):
        import torch
        with torch.no_grad():
            for e, m in zip(self.module.state_dict().values(), model.state_dict().values()):
                if e.dtype.is_floating_point:
                    e.mul_(self.decay).add_(m.detach(), alpha=1 - self.decay)
                else:
                    e.copy_(m)

    def state_dict(self):
        return self.module.state_dict()

    def load_state_dict(self, sd):
        self.module.load_state_dict(sd)


def validate(model, vids, device, max_frames=1800):
    """Doğrulama videolarının ilk 60 s'sinde pencere MAE (argmax; --val-viterbi ile Viterbi)."""
    errs, groups = [], {}
    for v in vids:
        frames = np.load(v["npy"], mmap_mode="r")[:max_frames]
        bvp = np.load(v["npz"])["bvp"][:max_frames]
        pred = predict_video(model, np.asarray(frames), device)
        if pred is None:
            continue
        c, hr_a, hr_v = hr_from_bvp(pred)
        errs.append(np.mean(np.abs((hr_v if VAL_VITERBI else hr_a) - reference_hr(bvp, c))))
        groups.setdefault(f"{v['source']}/{v['camera']}", []).append(errs[-1])
    VAL_GROUPS.clear()
    VAL_GROUPS.update({k: (float(np.mean(e)), len(e)) for k, e in sorted(groups.items())})
    return float(np.mean(errs)) if errs else float("nan")


def main():
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dl")
    ap.add_argument("--out", default="results/derin_ogrenme/egitim")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=600, help="epoch başına adım")
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--deadline", default="", help='"YYYY-MM-DD HH:MM": bu saatte güvenle dur')
    ap.add_argument("--val-max", type=int, default=40, help="doğrulamada en çok kaç video")
    ap.add_argument("--init", default="", help="last.pth yoksa bu ağırlıklardan başla (yeni veriyle ince ayar turu); "
                                               "varsayılan: PURE ön-eğitimli")
    ap.add_argument("--no-clean", action="store_true", help="etiket kalitesi filtresini kapat")
    ap.add_argument("--phone-aug", action="store_true", help="telefon benzeri bozulmalar (phone_degrade)")
    ap.add_argument("--arch", choices=ARCHS, default="factorizephys")
    ap.add_argument("--scratch", action="store_true", help="rastgele başlat (mmrphys'te her zaman)")
    ap.add_argument("--source-weights", default="", metavar="mcd=0.7,vipl=0.15,...",
                    help="veri setlerinin eğitimdeki payı (varsayılan: kare sayısıyla orantılı)")
    ap.add_argument("--loss", choices=tuple(LOSSES), default="", help="varsayılan: factorizephys pearson, "
                                                                        "mmrphys smoothl1 (makaledeki gibi)")
    ap.add_argument("--spec-loss", type=float, default=0.0, metavar="W",
                    help="kayıp = negatif Pearson + W * spektral KL (ör. 0.2; harmonik hatasında KL ~14 olabilir); 0: kapalı (eski davranış)")
    ap.add_argument("--ema", type=float, default=0.0, metavar="D",
                    help="ağırlıkların üstel hareketli ortalaması (ör. 0.999); doğrulama ve best.pth EMA ağırlıklarıyla. "
                         "0: kapalı")
    ap.add_argument("--val-viterbi", action="store_true", help="en iyi epoch'u Viterbi MAE ile seç (varsayılan argmax)")
    ap.add_argument("--amp", action="store_true",
                    help="karışık hassasiyet (float16, yalnızca CUDA): T4'te ~2x hız. Kayıp NaN olursa kapatın")
    ap.add_argument("--speed", type=float, nargs=2, default=[0.8, 1.25], metavar=("MIN", "MAX"),
                    help="hız artırma aralığı (ör. 0.7 1.5: yüksek nabız örneklerini çoğaltır)")
    ap.add_argument("--box-jitter", type=float, default=0.0, metavar="J",
                    help="yüz kutusu kayması artırması: kırpıntı ±J ölçek ve kayma (ör. 0.1); 0: kapalı")
    ap.add_argument("--hr-balance", type=float, default=0.0, metavar="K",
                    help="nabız aralığına göre dengeli örnekleme: seyrek nabızlı (ör. egzersiz sonrası 120+) videolar "
                         "en fazla K kat sık seçilir (ör. 3); 0: kapalı")
    a = ap.parse_args()
    global CLEAN, PHONE_AUG, SOURCE_WEIGHTS, VAL_VITERBI, SPEED, MAX_SPAN, HR_BALANCE, BOX_JITTER
    CLEAN = not a.no_clean
    PHONE_AUG = a.phone_aug
    SOURCE_WEIGHTS = {k: float(x) for k, x in (kv.split("=") for kv in a.source_weights.split(",") if kv)}
    VAL_VITERBI = a.val_viterbi
    SPEED = (a.speed[0], a.speed[1])
    MAX_SPAN = int(np.ceil(CHUNK * SPEED[1])) + 1
    HR_BALANCE = a.hr_balance
    BOX_JITTER = a.box_jitter
    deadline = datetime.strptime(a.deadline, "%Y-%m-%d %H:%M").timestamp() if a.deadline else float("inf")

    os.makedirs(a.out, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vids = list_videos(a.data)
    train = [v for v in vids if not is_val(v["person"])]
    val = pick_val(vids, a.val_max)
    print(f"eğitim {len(train)} video ({len({v['person'] for v in train})} kişi), "
          f"doğrulama {len(val)} video, cihaz {device}", flush=True)
    if train:
        h = np.array([v["hr"] for v in train])
        edges = [40, 70, 90, 110, 130, 250]
        print("  eğitim nabız dağılımı: " + ", ".join(
            f"{lo}-{hi}: {int(((h >= lo) & (h < hi)).sum())}" for lo, hi in zip(edges, edges[1:])), flush=True)
    if not train:
        raise SystemExit("Eğitim verisi yok: önce scripts/dl_prepare.py --mcd N")

    scratch = a.scratch or (a.arch != "factorizephys" and not a.init)  # MMRPhys'in hazır ağırlığı kodla uyumsuz
    init = None if scratch else (a.init or PRETRAINED)
    model = build_model(device, init, arch=a.arch)
    loss_fn = LOSSES[a.loss or ("pearson" if a.arch == "factorizephys" else "smoothl1")]
    with_label = a.arch == "mmrphys"  # TSFM eğitimde etiketi kısıt olarak kullanır
    print(f"mimari {a.arch} ({sum(p.numel() for p in model.parameters())} parametre), "
          f"{'rastgele başlatma' if scratch else 'başlangıç ağırlıkları: ' + init}, kayıp {loss_fn.__name__}",
          flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    use_amp = a.amp and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    ema = None
    if a.ema > 0:  # AveragedModel modeli deepcopy ile kopyalar; MMRPhys'te kopyalanamayan tensör özellikleri var
        twin = build_model(device, init, arch=a.arch)
        twin.load_state_dict(model.state_dict())
        ema = EMA(twin, a.ema)

    def eval_model():  # doğrulanan ve best.pth'e yazılan model
        return ema.module if ema is not None else model
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr / 50)
    state = {"epoch": 0, "best": None, "history": []}
    last = os.path.join(a.out, "last.pth")

    def remeasure_best(state, val):
        """Doğrulama kümesi değiştiyse en iyi modeli yeni kümede yeniden ölçer (karşılaştırma aynı kümede olsun)."""
        names = sorted(v["npz"] for v in val)
        if not val or state.get("val_set") == names:
            return
        state["val_set"] = names
        if state["best"] is None or not os.path.exists(os.path.join(a.out, "best.pth")):
            return
        best_model = build_model(device, os.path.join(a.out, "best.pth"))
        state["best"]["val_mae"] = validate(best_model, val, device)
        del best_model
        print(f"  doğrulama kümesi değişti ({len(val)} video); en iyi (epoch {state['best']['epoch']}) "
              f"yeniden ölçüldü: {state['best']['val_mae']:.2f} BPM", flush=True)

    if os.path.exists(last):
        ck = torch.load(last, map_location=device)
        model.load_state_dict(ck["model"], strict=False)
        if ema is not None:
            if "ema" in ck:
                ema.load_state_dict(ck["ema"])
            else:  # EMA'sız kontrol noktasından devam: ortalama güncel ağırlıklardan başlar
                ema.module.load_state_dict(model.state_dict())
        sched.load_state_dict(ck["sched"])
        try:
            opt.load_state_dict(ck["opt"])
        except (ValueError, KeyError, TypeError):  # onarılmış kontrol noktası: taze optimizer, kaldığı öğrenme oranı
            for g in opt.param_groups:
                g["lr"] = sched.get_last_lr()[0]
            print("  optimizer durumu yok/uyumsuz: taze optimizer", flush=True)
        state = ck["state"]
        print(f"devam: epoch {state['epoch']}", flush=True)
        val = pick_val(vids, a.val_max, state.get("val_set", ()))  # önceki oturumun doğrulama videoları korunur
        remeasure_best(state, val)
    elif val:
        mae0 = validate(eval_model(), val, device)
        print(f"başlangıç modeli doğrulama MAE: {mae0:.2f} BPM", flush=True)
        print("  doğrulama: " + ", ".join(f"{k} {m:.2f} ({n})" for k, (m, n) in VAL_GROUPS.items()), flush=True)
        state["history"].append({"epoch": 0, "val_mae": mae0, "loss": None})
        state["best"] = {"epoch": 0, "val_mae": mae0}
        torch.save({"model": eval_model().state_dict(), "arch": a.arch, "init": init}, os.path.join(a.out, "best.pth"))
    state["val_set"] = sorted(v["npz"] for v in val)
    state["ayarlar"] = {k: v for k, v in vars(a).items() if k not in ("data", "out", "deadline")}  # rapor için

    sampler = ChunkSampler(train)
    epoch_time = None
    while state["epoch"] < a.epochs:
        if time.time() > deadline or (epoch_time and time.time() + epoch_time > deadline):
            print(f"süre sınırı: eğitim durduruldu [{datetime.now():%H:%M:%S}]", flush=True)
            break
        t0 = time.time()
        allv = list_videos(a.data)  # indirme/hazırlama/hizalama sürerken gelenler
        new = [v for v in allv if not is_val(v["person"])]
        if {v["npz"] for v in new} != {v["npz"] for v in train}:
            train = new
            sampler = ChunkSampler(train)
            print(f"  eğitim kümesi: {len(train)} video ({len({v['person'] for v in train})} kişi)", flush=True)
        val = pick_val(allv, a.val_max, state.get("val_set", ()))
        remeasure_best(state, val)
        model.train()
        losses = []
        pf = Prefetcher(sampler, a.bs, seed=100000 * state["epoch"] + 1234)
        for step in range(a.steps):
            x, y, prm = pf.next()
            x = gpu_augment(x, prm, device)
            y = torch.as_tensor(y, device=device)
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                pred = model(x, label_bvp=y)[0] if with_label else model(x)[0]
            pred = pred.float()  # kayıplar float32'de (Pearson/FFT float16'da kararsız)
            loss = loss_fn(pred, y)
            if a.spec_loss > 0:
                loss = loss + a.spec_loss * spectral_kl(pred, y)
            if not torch.isfinite(loss):
                continue
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            if not torch.isfinite(gnorm):  # sayısal patlama: bu adımı atla
                opt.zero_grad(set_to_none=True)
                scaler.update()
                continue
            scaler.step(opt)
            scaler.update()
            sched.step()
            if ema is not None:
                ema.update_parameters(model)
            losses.append(loss.item())
            if (step + 1) % 100 == 0:
                print(f"  epoch {state['epoch'] + 1} adım {step + 1}/{a.steps} kayıp {np.mean(losses[-100:]):.4f}",
                      flush=True)
        pf.close()
        if not all(torch.isfinite(q).all() for q in model.parameters()):  # ağırlıklar bozulduysa en iyiye dön
            print(f"  UYARI: ağırlıklar NaN oldu; en iyi modele dönülüyor, optimizer sıfırlanıyor "
                  f"[{datetime.now():%H:%M:%S}]", flush=True)
            model.load_state_dict(torch.load(os.path.join(a.out, "best.pth"), map_location=device)["model"])
            opt = torch.optim.AdamW(model.parameters(), lr=sched.get_last_lr()[0], weight_decay=1e-4)
            sched.optimizer = opt
            if ema is not None:
                ema.module.load_state_dict(model.state_dict())
            continue
        state["epoch"] += 1
        mae = validate(eval_model(), val, device) if val else float("nan")
        state["history"].append({"epoch": state["epoch"], "val_mae": mae, "loss": float(np.mean(losses))})
        if state["best"] is None or mae < state["best"]["val_mae"]:
            state["best"] = {"epoch": state["epoch"], "val_mae": mae}
            torch.save({"model": eval_model().state_dict(), "arch": a.arch, "init": init}, os.path.join(a.out, "best.pth"))
        ck = {"model": model.state_dict(), "arch": a.arch, "init": init, "opt": opt.state_dict(),
              "sched": sched.state_dict(), "state": state}
        if ema is not None:
            ck["ema"] = ema.state_dict()
        torch.save(ck, last + ".part")
        os.replace(last + ".part", last)
        epoch_time = time.time() - t0
        print(f"epoch {state['epoch']}: kayıp {np.mean(losses):.4f}, doğrulama MAE {mae:.2f} BPM, "
              f"en iyi {state['best']['val_mae']:.2f} (epoch {state['best']['epoch']}), {epoch_time:.0f} s "
              f"[{datetime.now():%H:%M:%S}]", flush=True)
        print("  doğrulama: " + ", ".join(f"{k} {m:.2f} ({n})" for k, (m, n) in VAL_GROUPS.items()), flush=True)
        json.dump(state, open(os.path.join(a.out, "gecmis.json"), "w"), indent=1)
    print("bitti", flush=True)


if __name__ == "__main__":
    main()
