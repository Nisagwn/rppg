"""Derin öğrenme betikleri için ortak parçalar: rPPG-Toolbox FactorizePhys modeli, çıkarım, HR tahmini."""
import os
import sys
import types

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLBOX = os.path.join(ROOT, "external", "rPPG-Toolbox")
sys.path.insert(0, ROOT)
sys.path.insert(0, TOOLBOX)
sys.modules.setdefault("neurokit2", types.ModuleType("neurokit2"))  # FSAM.py içe aktarıyor, kullanmıyor

from rppg.filtering import preprocess_bvp  # noqa: E402
from rppg.hr import BPM_GRID, argmax_track, spectrogram, viterbi_track  # noqa: E402
from rppg.io_utils import gt_window_hr  # noqa: E402

CHUNK = 160
PRETRAINED = os.path.join(TOOLBOX, "final_model_release", "PURE_FactorizePhys_FSAM_Res.pth")
MD_CONFIG = {"FRAME_NUM": CHUNK, "MD_TYPE": "NMF", "MD_FSAM": True, "MD_TRANSFORM": "T_KAB",
             "MD_S": 1, "MD_R": 1, "MD_STEPS": 4, "MD_INFERENCE": True, "MD_RESIDUAL": True}


def build_model(device, weights=PRETRAINED, dropout=0.1):
    import torch
    from neural_methods.model.FactorizePhys.FactorizePhys import FactorizePhys
    model = FactorizePhys(frames=CHUNK, md_config=dict(MD_CONFIG), in_channels=3, dropout=dropout, device=device)
    if weights:
        sd = torch.load(weights, map_location=device)
        sd = sd.get("model", sd)
        sd = {k.removeprefix("module."): v for k, v in sd.items()}
        missing, unexpected = model.load_state_dict(sd, strict=False)
        if missing or unexpected:
            print(f"  ağırlık uyarısı: eksik {len(missing)}, fazla {len(unexpected)}")
    return model.to(device)


def to_input(frames_uint8, device):
    """[B,T,72,72,3] uint8 -> [B,3,T+1,72,72] float (toolbox: son kare tekrarlanır, model içinde diff alınır)."""
    import torch
    x = torch.as_tensor(np.ascontiguousarray(frames_uint8), device=device).float()
    x = x.permute(0, 4, 1, 2, 3)
    return torch.cat([x, x[:, :, -1:]], dim=2)


def predict_video(model, frames, device, batch=4):
    """Tüm video için BVP: ardışık 160 karelik parçalar; son parça sona hizalanıp eksik kısmı alınır."""
    import torch
    n = len(frames)
    if n < CHUNK:
        return None
    starts = list(range(0, n - CHUNK + 1, CHUNK))
    if starts[-1] + CHUNK < n:
        starts.append(n - CHUNK)
    out = np.zeros(n, dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for i in range(0, len(starts), batch):
            ss = starts[i:i + batch]
            x = to_input(np.stack([frames[s:s + CHUNK] for s in ss]), device)
            y = model(x)[0].float().cpu().numpy()
            for s, yy in zip(ss, y):
                yy = (yy - yy.mean()) / (yy.std() + 1e-8)
                if s % CHUNK:  # sona hizalı son parça: yalnızca önceki parçaların kapsamadığı kısım
                    done = (n // CHUNK) * CHUNK
                    out[done:] = yy[done - s:]
                else:
                    out[s:s + CHUNK] = yy
    return out


def hr_from_bvp(bvp, fs=30.0, win=10.0, step=1.0):
    x = preprocess_bvp(bvp, fs)
    centers, S = spectrogram(x, fs, win, step)
    return centers, argmax_track(S, BPM_GRID), viterbi_track(S, BPM_GRID, step)


def reference_hr(label, centers, fs=30.0, win=10.0):
    t = np.arange(len(label)) / fs
    return gt_window_hr({"bvp": label, "t": t}, centers, win, fs)
