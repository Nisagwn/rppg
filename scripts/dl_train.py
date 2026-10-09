#!/usr/bin/env python
"""
FactorizePhys (rPPG-Toolbox, NeurIPS 2024) ince ayarı: PURE ön-eğitimli ağırlıklardan başlayıp
MCD-rPPG (3 kamera, dinlenme + egzersiz) ve UBFC-rPPG'nin test DIŞI kişileriyle eğitir.

* Veri: scripts/dl_prepare.py çıktıları (data/dl/mcd, data/dl/ubfc). Kişi bazında ayrım:
  kişilerin ~%10'u doğrulama, geri kalanı eğitim. Test kişileri zaten hiç işlenmemiştir.
* Her epoch: videolardan rastgele başlangıçlı 160 karelik parçalar (uzunlukla orantılı örnekleme).
* Artırma: yatay çevirme, hız değişimi (0.8–1.25x; HR dağılımını genişletir), parlaklık ölçeği.
* Kayıp: örnek başına negatif Pearson. MCD etiketi ters çevrilir (bkz. ChunkSampler).
* Seçim: doğrulama videolarında pencere MAE (argmax, 10 s) en düşük epoch -> best.pth
* Dayanıklılık: her epoch sonunda last.pth (model + optimizer + zamanlayıcı); tekrar çalıştırınca devam eder.
  --deadline "2026-09-28 04:15" verilirse o saatte güvenle durur.

    python scripts/dl_train.py --epochs 30 --steps 600 --deadline "2026-09-28 04:15"

İsteğe bağlı iyileştirmeler (hepsi varsayılan olarak kapalı; kapalıyken davranış öncekiyle aynı):
  --spec-loss 0.2     frekans alanı kaybı (spectral_kl): yanlış frekansa/harmoniğe kilitlenmeyi cezalandırır
  --ema 0.999         ağırlık ortalaması; doğrulama ve best.pth bununla (tek şanslı epoch'a bağlı seçimi azaltır)
  --val-viterbi       en iyi epoch'u raporlanan yöntemle (Viterbi) seç
  --amp               float16 karışık hassasiyet (CUDA), T4'te daha hızlı
  --speed 0.7 1.5     daha geniş hız artırması (yüksek nabız örnekleri)
"""
import argparse
import glob
import json
import os
import time
import zlib
from datetime import datetime

import numpy as np

from dl_common import (CHUNK, PER_VIDEO_SYNC, build_model, hr_from_bvp, label_shift, predict_video, reference_hr,
                       shift_label, video_decision)
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
    source = str(m["source"])
    q = quality(p) if CLEAN else None  # etiket kalitesi (dl_quality.py); yoksa burada hesaplanıp .kal yazılır
    if q is not None and not video_decision(q, source):
        return None
    return {"npz": p, "npy": p[:-4] + ".npy", "n": int(m["n"]), "person": str(m["person"]),
            "source": source, "camera": str(m["camera"]), "q": q,
            "vote": float(m["polarity"]) * float(m["polarity_corr"]) if "polarity" in m.files else 0.0}


TRAIN_SOURCES = ("mcd", "ubfc", "pure", "ubfcphys", "mpu", "mmpd", "vipl", "cohface", "dlcn")  # test_* klasörleri hiç okunmaz


def list_videos(root, min_face=0.5):
    vids = []
    for p in sorted(p for sub in TRAIN_SOURCES
                    for p in glob.glob(os.path.join(root, sub, "*.npz"))):
        mt = os.path.getmtime(p)
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
        v["shift"] = label_shift(v["q"], v["source"], v["camera"]) if CLEAN else 0
        if CLEAN and v["source"] in PER_VIDEO_SYNC:
            v["mult"] = 1.0  # işaret yerine hizalama: tepe korelasyonu pozitif olacak şekilde kaydırıldı
    return vids


SPEED = (0.8, 1.25)  # hız artırma aralığı (--speed); >1 nabzı hızlandırır
MAX_SPAN = int(np.ceil(CHUNK * SPEED[1])) + 1  # en hızlı artırmada gereken kare sayısı


def is_val(person):
    return zlib.crc32(person.encode()) % 10 == 0


class ChunkSampler:
    def __init__(self, vids):
        self.vids = vids
        w = np.array([v["n"] for v in vids], dtype=float)
        self.p = w / w.sum()
        self.cache = {}

    def _frames(self, v):
        item = self.cache.get(v["npy"])
        if item is None:  # iş parçacıkları arasında güvenli: çift tek seferde yazılır
            bvp = np.load(v["npz"])["bvp"]
            # MCD parmak PPG'si UBFC/PURE'a göre ters işaretli (ön-eğitimli modelle korelasyon ~ -0.75, gecikme ~0);
            # diğer veri setleri için çarpan list_videos'ta belirlenir
            kal = v["npz"][:-4] + ".kal"
            ok = np.load(kal)["frame_ok"] if CLEAN and os.path.exists(kal) else np.ones(len(bvp), bool)
            bvp = shift_label(bvp, v.get("shift", 0))  # etiket-video zaman hizası (dl_common.CAMERA_SHIFT)
            item = (np.load(v["npy"], mmap_mode="r"), v.get("mult", 1.0) * bvp, ok)
            self.cache[v["npy"]] = item
        return item

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
        if PHONE_AUG and torch.rand(()) < 0.6:
            c = phone_degrade(c)
        out.append(c)
    x = torch.stack(out).permute(0, 4, 1, 2, 3)
    return torch.cat([x, x[:, :, -1:]], dim=2)


PHONE_AUG = False  # --phone-aug


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


VAL_GROUPS = {}  # son doğrulamanın kaynak/kamera bazında MAE'si (günlüğe yazılır)


VAL_VITERBI = False  # --val-viterbi: seçim, raporlanan yöntemle (Viterbi) aynı ölçütle yapılır


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
    a = ap.parse_args()
    global CLEAN, PHONE_AUG, VAL_VITERBI, SPEED, MAX_SPAN
    CLEAN = not a.no_clean
    PHONE_AUG = a.phone_aug
    VAL_VITERBI = a.val_viterbi
    SPEED = (a.speed[0], a.speed[1])
    MAX_SPAN = int(np.ceil(CHUNK * SPEED[1])) + 1
    deadline = datetime.strptime(a.deadline, "%Y-%m-%d %H:%M").timestamp() if a.deadline else float("inf")

    os.makedirs(a.out, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vids = list_videos(a.data)
    train = [v for v in vids if not is_val(v["person"])]
    val = [v for v in vids if is_val(v["person"])]
    val = [val[i] for i in np.linspace(0, len(val) - 1, min(a.val_max, len(val))).astype(int)] if val else []
    print(f"eğitim {len(train)} video ({len({v['person'] for v in train})} kişi), "
          f"doğrulama {len(val)} video, cihaz {device}", flush=True)
    if not train:
        raise SystemExit("Eğitim verisi yok: önce scripts/dl_prepare.py --mcd N")

    model = build_model(device, a.init) if a.init else build_model(device)
    if a.init:
        print(f"başlangıç ağırlıkları: {a.init}", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    use_amp = a.amp and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    ema = None
    if a.ema > 0:
        from torch.optim.swa_utils import AveragedModel, get_ema_multi_avg_fn
        ema = AveragedModel(model, multi_avg_fn=get_ema_multi_avg_fn(a.ema), use_buffers=True)

    def eval_model():  # doğrulanan ve best.pth'e yazılan model
        return ema.module if ema is not None else model
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr / 50)
    state = {"epoch": 0, "best": None, "history": []}
    last = os.path.join(a.out, "last.pth")
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
        names = sorted(v["npz"] for v in val)
        if val and state.get("val_set") != names:  # doğrulama kümesi değişti: en iyiyi yeni kümede yeniden ölç
            best_model = build_model(device, os.path.join(a.out, "best.pth"))
            state["best"]["val_mae"] = validate(best_model, val, device)
            del best_model
            print(f"  doğrulama kümesi değişti ({len(val)} video); en iyi (epoch {state['best']['epoch']}) "
                  f"yeniden ölçüldü: {state['best']['val_mae']:.2f} BPM", flush=True)
    elif val:
        mae0 = validate(eval_model(), val, device)
        print(f"başlangıç modeli doğrulama MAE: {mae0:.2f} BPM", flush=True)
        print("  doğrulama: " + ", ".join(f"{k} {m:.2f} ({n})" for k, (m, n) in VAL_GROUPS.items()), flush=True)
        state["history"].append({"epoch": 0, "val_mae": mae0, "loss": None})
        state["best"] = {"epoch": 0, "val_mae": mae0}
        torch.save({"model": eval_model().state_dict()}, os.path.join(a.out, "best.pth"))
    state["val_set"] = sorted(v["npz"] for v in val)

    sampler = ChunkSampler(train)
    epoch_time = None
    while state["epoch"] < a.epochs:
        if time.time() > deadline or (epoch_time and time.time() + epoch_time > deadline):
            print(f"süre sınırı: eğitim durduruldu [{datetime.now():%H:%M:%S}]", flush=True)
            break
        t0 = time.time()
        new = [v for v in list_videos(a.data) if not is_val(v["person"])]  # indirme sürerken yeni gelenler
        if len(new) > len(train):
            train = new
            sampler = ChunkSampler(train)
            print(f"  eğitim kümesi: {len(train)} video ({len({v['person'] for v in train})} kişi)", flush=True)
        model.train()
        losses = []
        pf = Prefetcher(sampler, a.bs, seed=100000 * state["epoch"] + 1234)
        for step in range(a.steps):
            x, y, prm = pf.next()
            x = gpu_augment(x, prm, device)
            y = torch.as_tensor(y, device=device)
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                pred = model(x)[0]
            pred = pred.float()  # kayıplar float32'de (Pearson/FFT float16'da kararsız)
            loss = neg_pearson(pred, y)
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
            torch.save({"model": eval_model().state_dict()}, os.path.join(a.out, "best.pth"))
        ck = {"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(), "state": state}
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
