#!/usr/bin/env python
"""
Eğitimi canlı izleme paneli (yerel, bağımlılıksız): http://localhost:8765

Günlükleri (data/dl/logs) ve veri klasörlerini okur; hiçbir şeye yazmaz, eğitimi etkilemez.

    python scripts/dl_panel.py            # sonra tarayıcıda http://localhost:8765
    python scripts/dl_panel.py --port 9000
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS = os.path.join(ROOT, "data", "dl", "logs")
EPOCH_RE = re.compile(r"^epoch (\d+): kayıp ([\d.na]+), doğrulama MAE ([\d.na]+) BPM, en iyi ([\d.]+) \(epoch (\d+)\), (\d+) s")
STEP_RE = re.compile(r"^\s+epoch (\d+) adım (\d+)/(\d+) kayıp ([\d.na]+)")
RUN_RE = re.compile(r"^===== (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) başlatma")
CLOCK_RE = re.compile(r"\[(\d\d:\d\d:\d\d)\]")
RESET_RE = re.compile(r"doğrulama kümesi değişti \((\d+) video\); en iyi \(epoch (\d+)\) yeniden ölçüldü: ([\d.]+)")
PREP_RE = re.compile(r"\[(\d+)/(\d+)\]")


def _read(path, tail=None):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    return lines[-tail:] if tail else lines


def _num(s):
    try:
        v = float(s)
        return v if v == v else None
    except ValueError:
        return None


def _clock(line, run_start, elapsed):
    """Satırdaki [SS:DD:ss] saati; yoksa çalıştırma başlangıcı + geçen epoch süreleri (yaklaşık)."""
    if m := CLOCK_RE.search(line):
        return m[1][:5], False
    if run_start is None:
        return None, True
    return (run_start + timedelta(seconds=elapsed)).strftime("%H:%M"), True


def training_state():
    epochs, resets, current, train_size, events = {}, [], None, None, []
    run_start, elapsed, in_tb = None, 0, False
    for line in _read(os.path.join(LOGS, "egitim.log")):
        if m := RUN_RE.match(line):
            run_start, elapsed, in_tb = datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S"), 0, False
            continue
        if in_tb and line and not line.startswith((" ", "Traceback")):  # hata mesajının kendisi
            events[-1]["text"] = line.strip()[:200]
            in_tb = False
        if m := EPOCH_RE.match(line):
            e = int(m[1])
            elapsed += int(m[6])
            epochs[e] = {"epoch": e, "loss": _num(m[2]), "val": _num(m[3]), "best": float(m[4]),
                         "best_epoch": int(m[5]), "sec": int(m[6])}
            current = None
        elif m := STEP_RE.match(line):
            current = {"epoch": int(m[1]), "step": int(m[2]), "steps": int(m[3]), "loss": _num(m[4])}
        elif m := RESET_RE.search(line):
            resets.append({"after_epoch": max(epochs) if epochs else 0, "val": float(m[3]), "best_epoch": int(m[2])})
        elif "eğitim kümesi:" in line or line.startswith("eğitim "):
            train_size = line.strip()
        elif "UYARI" in line or line.startswith("Traceback") or "süre sınırı" in line:
            kind = "hata" if line.startswith("Traceback") else "uyarı" if "UYARI" in line else "olay"
            t, approx = _clock(line, run_start, elapsed)
            events.append({"time": t, "approx": approx, "kind": kind, "text": line.strip()[:200],
                           "day": run_start.strftime("%d.%m") if run_start else "", "run": str(run_start)})
            in_tb = kind == "hata"
    for ev in events:
        ev["current"] = ev["run"] == str(run_start)
    return {"epochs": sorted(epochs.values(), key=lambda x: x["epoch"]), "resets": resets,
            "current": current, "train_size": train_size, "events": events[-8:][::-1],
            "run_start": run_start.strftime("%d.%m %H:%M") if run_start else None}


def data_state():
    out = {}
    for sub in ("mcd", "ubfc", "pure"):
        out[sub] = len(glob.glob(os.path.join(ROOT, "data", "dl", sub, "*.npz")))
    prep = {}
    for name in ("hazirla_mcd", "hazirla_ubfc", "hazirla_pure"):
        done = os.path.exists(os.path.join(LOGS, name + ".done"))
        last = None
        for line in reversed(_read(os.path.join(LOGS, name + ".log"), 200)):
            if m := PREP_RE.search(line):
                last = {"k": int(m[1]), "n": int(m[2])}
                break
        prep[name.split("_")[1]] = {"done": done, "progress": last}
    return {"counts": out, "prep": prep}


def gpu_state():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5,
                           creationflags=0x08000000)
        u, mu, mt, t = [x.strip() for x in r.stdout.strip().split(",")]
        return {"util": int(u), "mem": int(mu), "mem_total": int(mt), "temp": int(t)}
    except Exception:
        return None


def state():
    du = shutil.disk_usage(ROOT)
    return {"train": training_state(), "data": data_state(), "gpu": gpu_state(),
            "disk": {"free_gb": du.free / 1e9, "total_gb": du.total / 1e9},
            "pipeline": _read(os.path.join(LOGS, "pipeline.log"), 12)}


PAGE = r"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>rPPG Eğitim Paneli</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1c2330;--mut:#687385;--line:#e3e6eb;--a:#2f6fdf;--b:#d9822b;--ok:#2f9e5b;--bad:#d64545}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1b2029;--fg:#e6e9ef;--mut:#8d97a8;--line:#2a313d;--a:#6fa0ff;--b:#f0a45a;--ok:#4cc27d;--bad:#ff6b6b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.k{color:var(--mut);font-size:12px}.v{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:8px}.bar>i{display:block;height:100%;background:var(--a)}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px;margin-bottom:12px}
svg{width:100%;height:220px;display:block}.ax{stroke:var(--line)}.tl{fill:var(--mut);font-size:11px}
pre{margin:0;white-space:pre-wrap;font:12px/1.5 ui-monospace,Consolas,monospace;color:var(--mut)}
.ok{color:var(--ok)}.bad{color:var(--bad)}h2{font-size:14px;margin:0 0 8px}
</style></head><body><main>
<h1>rPPG model eğitimi</h1><div class="sub" id="sub">yükleniyor…</div>
<div class="grid" id="cards"></div>
<div class="charts">
 <div class="card"><h2>Doğrulama hatası (MAE, BPM) — düşük iyi</h2><svg id="cv"></svg></div>
 <div class="card"><h2>Eğitim kaybı (1 − Pearson) — düşük iyi</h2><svg id="cl"></svg></div>
</div>
<div class="charts">
 <div class="card"><h2>Veri hazırlama</h2><div id="prep"></div></div>
 <div class="card"><h2>Yönetici günlüğü</h2><pre id="log"></pre></div>
</div>
<div class="sub">Kesik dikey çizgi: doğrulama kümesi değişti (yeni kişiler eklendi); çizginin iki yanındaki değerler doğrudan karşılaştırılamaz. Sayfa 10 saniyede bir yenilenir.</div>
</main><script>
const $=id=>document.getElementById(id), f1=v=>v==null?"–":v.toFixed(2);
function chart(el,pts,key,color,resets){
  const W=el.clientWidth||600,H=220,L=36,R=8,T=10,B=24; el.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const xs=pts.filter(p=>p[key]!=null); if(!xs.length){el.innerHTML="";return}
  const x0=Math.min(...pts.map(p=>p.epoch)),x1=Math.max(...pts.map(p=>p.epoch))||1;
  let ys=xs.map(p=>p[key]); const s=[...ys].sort((a,b)=>a-b); let y1=Math.min(s[Math.floor(s.length*.95)]*1.1,Math.max(...ys)),y0=Math.min(...ys)*.9;
  if(y1<=y0)y1=y0+1;
  const X=e=>L+(e-x0)/((x1-x0)||1)*(W-L-R),Y=v=>T+(1-(Math.min(v,y1)-y0)/(y1-y0))*(H-T-B);
  let g="";for(let i=0;i<=4;i++){const v=y0+(y1-y0)*i/4;g+=`<line class="ax" x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tl" x="2" y="${Y(v)+4}">${v.toFixed(2)}</text>`}
  for(const r of resets)g+=`<line x1="${X(r.after_epoch)}" x2="${X(r.after_epoch)}" y1="${T}" y2="${H-B}" stroke="var(--mut)" stroke-dasharray="4 4"/>`;
  g+=`<text class="tl" x="${L}" y="${H-6}">epoch ${x0}</text><text class="tl" x="${W-R}" y="${H-6}" text-anchor="end">${x1}</text>`;
  const d=xs.map((p,i)=>(i?"L":"M")+X(p.epoch).toFixed(1)+","+Y(p[key]).toFixed(1)).join("");
  g+=`<path d="${d}" fill="none" stroke="${color}" stroke-width="2"/>`;
  for(const p of xs)g+=`<circle cx="${X(p.epoch)}" cy="${Y(p[key])}" r="2.5" fill="${color}"><title>epoch ${p.epoch}: ${p[key].toFixed(3)}</title></circle>`;
  el.innerHTML=g;
}
async function tick(){
  let s; try{s=await (await fetch("/api",{cache:"no-store"})).json()}catch(e){$("sub").textContent="Panel sunucusuna ulaşılamıyor";return}
  const t=s.train,E=t.epochs,last=E[E.length-1],c=t.current;
  const best=last?`${last.best.toFixed(2)} BPM (epoch ${last.best_epoch})`:"–";
  const lastReset=t.resets[t.resets.length-1];
  $("sub").textContent=(t.train_size||"")+" · son güncelleme "+new Date().toLocaleTimeString("tr-TR");
  const cards=[
    ["En iyi doğrulama",best],
    ["Son epoch",last?`${last.epoch} · ${f1(last.val)} BPM`:"–"],
    ["Şu an",c?`epoch ${c.epoch} · ${c.step}/${c.steps}`:"doğrulama / hazırlık",c?c.step/c.steps:null],
    ["Epoch süresi",last?`${Math.round(last.sec/60)} dk`:"–"],
    ["GPU",s.gpu?`%${s.gpu.util} · ${s.gpu.temp}°C`:"–",s.gpu?s.gpu.util/100:null],
    ["Boş disk",`${s.disk.free_gb.toFixed(1)} GB`,1-s.disk.free_gb/s.disk.total_gb],
  ];
  $("cards").innerHTML=cards.map(([k,v,p])=>`<div class="card"><div class="k">${k}</div><div class="v">${v}</div>${p!=null?`<div class="bar"><i style="width:${Math.round(p*100)}%"></i></div>`:""}</div>`).join("")
    +(t.events.length?`<div class="card" style="grid-column:1/-1"><div class="k">Olaylar (en yeni üstte · şu anki çalıştırma ${t.run_start} başladı)</div>`
      +t.events.map(e=>`<div style="margin-top:6px;${e.current?"":"opacity:.55"}"><b>${e.day} ${e.approx?"~":""}${e.time||"?"}</b> `
        +`<span class="${e.kind==="olay"?"ok":"bad"}">[${e.kind}]</span> ${e.text.replace(/</g,"&lt;")}`
        +(e.text.startsWith("süre sınırı")?` <span class="k">— planlanan bitiş saatine ulaşıldı, normal</span>`:"")
        +(e.current?"":` <span class="k">(önceki çalıştırma)</span>`)+`</div>`).join("")
      +`<div class="k" style="margin-top:6px">~ = yaklaşık saat (çalıştırma başlangıcı + epoch süreleri)</div></div>`:"");
  chart($("cv"),E,"val","var(--a)",t.resets); chart($("cl"),E,"loss","var(--b)",t.resets);
  const P=s.data.prep,C=s.data.counts,names={mcd:"MCD-rPPG",ubfc:"UBFC-rPPG",pure:"PURE"};
  $("prep").innerHTML=Object.keys(names).map(k=>{const p=P[k],pr=p.progress;const frac=pr?pr.k/pr.n:0;
    return `<div style="margin-bottom:10px"><b>${names[k]}</b> · ${C[k]} video hazır ${p.done?'<span class="ok">✓ bitti</span>':pr?`· ${pr.k}/${pr.n}`:""}<div class="bar"><i style="width:${p.done?100:Math.round(frac*100)}%"></i></div></div>`}).join("");
  $("log").textContent=s.pipeline.join("\n");
}
tick();setInterval(tick,10000);addEventListener("resize",tick);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api"):
            body, ctype = json.dumps(state()).encode(), "application/json"
        else:
            body, ctype = PAGE.encode(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Panel: http://localhost:{a.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
