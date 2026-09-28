#!/usr/bin/env python
"""
Gece boyu derin öğrenme akışı: veri indirme/işleme -> eğitim -> değerlendirme.

Her adım yarıda kaldığı yerden devam eder. Bu betik tekrar tekrar çalıştırılabilir (Windows Görev
Zamanlayıcı 10 dakikada bir çağırır): başka bir kopya çalışıyorsa hemen çıkar; çöken adımları yeniden başlatır.
İş bitince zamanlanmış görevi siler. Günlükler: data/dl/logs/

    python scripts/dl_pipeline.py --train-until "2026-09-28 04:10" --finish "2026-09-28 04:45"
"""
import argparse
import ctypes
import glob
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS = os.path.join(ROOT, "data", "dl", "logs")
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
TASK = "rppg_dl_gece"
NO_WINDOW = 0x08000000


def alive(pid):
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


def log(msg):
    line = f"{datetime.now():%H:%M:%S} {msg}"
    print(line, flush=True)
    with open(os.path.join(LOGS, "pipeline.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


class Step:
    def __init__(self, name, args, max_runs=4):
        self.name, self.args, self.max_runs = name, args, max_runs
        self.pidfile = os.path.join(LOGS, name + ".pid")
        self.donefile = os.path.join(LOGS, name + ".done")
        self.proc = None

    @property
    def done(self):
        return os.path.exists(self.donefile)

    def running(self):
        if self.proc is not None:
            return self.proc.poll() is None
        if os.path.exists(self.pidfile):  # önceki yönetici kopyasının başlattığı süreç
            return alive(int(open(self.pidfile).read().strip() or 0))
        return False

    def runs(self):
        p = os.path.join(LOGS, self.name + ".runs")
        return int(open(p).read()) if os.path.exists(p) else 0

    def start(self):
        n = self.runs() + 1
        open(os.path.join(LOGS, self.name + ".runs"), "w").write(str(n))
        out = open(os.path.join(LOGS, self.name + ".log"), "a", encoding="utf-8")
        out.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} başlatma {n} =====\n")
        out.flush()
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.proc = subprocess.Popen([PY, "-u"] + self.args, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT,
                                     env=env, creationflags=NO_WINDOW)
        open(self.pidfile, "w").write(str(self.proc.pid))
        log(f"{self.name}: başladı (pid {self.proc.pid}, {n}. kez)")

    def finished_ok(self):
        """Süreç bittiyse: çıkış 0 -> tamam; değilse yeniden denenecek."""
        if self.proc is not None and self.proc.poll() is not None:
            code = self.proc.returncode
            self.proc = None
            if code == 0:
                open(self.donefile, "w").write(datetime.now().isoformat())
                log(f"{self.name}: bitti")
                return True
            log(f"{self.name}: çıkış kodu {code}, yeniden denenecek")
        return self.done

    def stop(self):
        pid = self.proc.pid if self.proc else (int(open(self.pidfile).read()) if os.path.exists(self.pidfile) else 0)
        if pid and alive(pid):
            subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
            log(f"{self.name}: durduruldu (süre)")
        self.proc = None


def n_ready(sub):
    return len(glob.glob(os.path.join(ROOT, "data", "dl", sub, "*.npz")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcd", type=int, default=90)
    ap.add_argument("--ubfc", type=int, default=10)
    ap.add_argument("--prep-until", default="2026-09-28 03:30")
    ap.add_argument("--train-until", default="2026-09-28 04:10")
    ap.add_argument("--finish", default="2026-09-28 04:45")
    ap.add_argument("--min-videos", type=int, default=150, help="eğitim başlamadan önce gereken video")
    a = ap.parse_args()
    ts = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp()  # noqa: E731
    prep_until, train_until, finish = ts(a.prep_until), ts(a.train_until), ts(a.finish)

    os.makedirs(LOGS, exist_ok=True)
    lock = os.path.join(LOGS, "pipeline.pid")
    if os.path.exists(lock):
        old = int(open(lock).read().strip() or 0)
        if old and old != os.getpid() and alive(old):
            return
    open(lock, "w").write(str(os.getpid()))
    # bu süreç yaşadıkça bilgisayar uykuya geçmesin (ES_CONTINUOUS | ES_SYSTEM_REQUIRED); çıkınca kendiliğinden kalkar
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    log("yönetici başladı")

    mcd = Step("hazirla_mcd", ["scripts/dl_prepare.py", "--mcd", str(a.mcd), "--workers", "6"], max_runs=12)
    ubfc = Step("hazirla_ubfc", ["scripts/dl_prepare.py", "--ubfc", str(a.ubfc), "--workers", "1"], max_runs=12)
    train = Step("egitim", ["scripts/dl_train.py", "--epochs", "200", "--steps", "500",
                            "--deadline", a.train_until], max_runs=8)
    ev = Step("degerlendirme", ["scripts/dl_evaluate.py"], max_runs=3)

    while True:
        now = time.time()
        for s in (mcd, ubfc):
            if s.done:
                continue
            if now > prep_until:
                if s.running():
                    s.stop()
                continue
            if not s.running() and not s.finished_ok() and s.runs() < s.max_runs:
                s.start()

        import shutil
        if not mcd.done and shutil.disk_usage(ROOT).free < 6e9:  # disk koruması
            if mcd.running():
                mcd.stop()
            open(mcd.donefile, "w").write("disk doldu")
            log("hazirla_mcd: boş alan < 6 GB, indirme durduruldu")

        ready = n_ready("mcd") + n_ready("ubfc")
        if not train.done and not train.running() and not train.finished_ok():
            if now < train_until - 300 and ready >= a.min_videos and train.runs() < train.max_runs:
                train.start()
            elif now >= train_until - 300 and os.path.exists(os.path.join(ROOT, "results/derin_ogrenme/egitim/best.pth")):
                open(train.donefile, "w").write("süre doldu")
        if train.running() and now > train_until + 600:  # eğitim kendi durmadıysa
            train.stop()
            open(train.donefile, "w").write("zorla durduruldu")

        if train.done and not ev.done and not ev.running() and not ev.finished_ok() and ev.runs() < ev.max_runs:
            for s in (mcd, ubfc):  # değerlendirme sırasında CPU/disk boşalsın
                if s.running():
                    s.stop()
            ev.start()

        if ev.done or now > finish + 1800:
            log("akış tamamlandı" if ev.done else "süre aşıldı, akış bırakıldı")
            subprocess.call(["schtasks", "/Delete", "/TN", TASK, "/F"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
            os.remove(lock)
            return
        time.sleep(30)


if __name__ == "__main__":
    sys.exit(main())
