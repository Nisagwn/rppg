#!/usr/bin/env python
"""İki paketlenmiş modeli aynı gerçek video kesitleriyle yerel Chrome'da sınar.

Telefon ölçümü değildir. Varsayılan: üç kamera, bir kişi, 40 s; tarayıcı WASM arka ucu.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd

from validate_mobile import clips, gt_window_hr, read_clip, write_y4m, E2E


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips", default="1020_FullHDwebcam_before,1020_IriunWebcam_before,1020_USBVideo_before")
    ap.add_argument("--duration", type=float, default=40)
    ap.add_argument("--out", default="results/mobil_pure_s1")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    items = clips(SimpleNamespace(mcd_cameras="FullHDwebcam,IriunWebcam,USBVideo", clips=a.clips, max_clips=None))
    if {c["ad"] for c in items} != set(a.clips.split(",")):
        raise RuntimeError("Seçilen ham test videoları yerelde eksik")
    rows = []
    for c in items:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            frames = read_clip(c["video"], c["s0"], a.duration, c.get("ts"))
            duration = len(frames) / 30
            y4m = str(Path(tmp) / "clip.y4m")
            write_y4m(y4m, frames)
            del frames
            for model in ("tur5", "pure"):
                name = c["ad"] + "_" + model
                result, log, diag = [out / (name + suffix) for suffix in ("_result.json", "_log.json", "_diag.json")]
                print(f"{c['ad']} / {model}: {duration:.1f} s tarayıcı denemesi", flush=True)
                cp = subprocess.run(["node", E2E, "--video", y4m, "--expect", "0", "--seconds", str(duration - 1),
                                     "--params", f"model={model}&ep=wasm", "--coi", "--result", str(result),
                                     "--log", str(log), "--diag", str(diag)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=duration + 90)
                (out / (name + ".txt")).write_text(cp.stdout + cp.stderr, encoding="utf-8")
                if not result.exists() or not log.exists():
                    raise RuntimeError(f"Tarayıcı koşusu tamamlanmadı: {name}")
                status = json.loads(result.read_text())
                dl = status["cam"]["dl"]
                if dl.get("model") != model or not dl["ready"] or dl["failed"]:
                    raise RuntimeError(f"İstenen model çalışmadı: {name}, {dl}")
                samples = [r for r in json.loads(log.read_text()) if 10 <= r["t"] <= duration - 1]
                if not samples:
                    raise RuntimeError(f"Ölçüm üretilmedi: {name}")
                t = np.array([r["t"] for r in samples])
                ref = gt_window_hr(c["gt"], c["s0"] + t - 5, 10)
                error = np.abs(np.array([r["hr"] for r in samples]) - ref)
                diagnostics = json.loads(diag.read_text())
                latency = [r["model_ms"] for r in diagnostics if r["t"] >= 10 and r.get("model_ms", 0) > 0]
                rows.append({"kesit": c["ad"], "kamera": c["kamera"], "model": model, "pencere": len(samples),
                             "MAE": float(error.mean()), "p5": float(100 * np.mean(error <= 5)),
                             "model_ms_medyan": float(np.median(latency)) if latency else dl["ms"],
                             "threads": dl["threads"]})
                pd.DataFrame(rows).to_csv(out / "kesitler.csv", index=False)
                print(f"  MAE {error.mean():.3f} BPM; {len(samples)} pencere", flush=True)
    table = pd.DataFrame(rows)
    report = ["# Yerel Chrome: PURE S1 / mevcut model", "",
              "Aynı ham MCD video kesitleri 30 fps sahte kamerayla uygulamaya verildi. Yüz bulma ve nabız takibi uygulamanın kendisidir.",
              "Her model ayrı, temiz tarayıcı oturumunda `ep=wasm` ve çapraz köken yalıtımıyla çalıştırıldı.",
              "Referans, aynı 10 s penceresindeki parmak PPG nabzıdır. İlk 10 s hariç; çıktı üretmeyen saniyeler pencere sayısına yansır.",
              "Süre sütunu saniyelik teşhis kayıtlarındaki son model çağrısının medyanıdır; telefon performansı değildir.",
              "Üç kesit tek kişidendir; genelleme veya istatistiksel üstünlük sonucu çıkarılamaz.",
              "Test aracı `--expect 0` kullandığı için konsoldaki BAŞARISIZ etiketi sıfır nabız beklentisine aittir; model yüklenmesi ve gerçek PPG hatası burada ayrıca kontrol edilir.", "",
              table.round(3).to_markdown(index=False), ""]
    (out / "SONUCLAR.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
