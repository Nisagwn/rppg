#!/usr/bin/env python
"""
Hazırlanmış eğitim verisini Hugging Face'teki gizli bir veri deposuyla eşitler (Kaggle oturumları arası taşıma).

Hazırlama ve eğitim ayrı oturumlarda yapılır (6. tur hazırlama + eğitim aynı anda çalışırken 4.6 saatte durdu):
  * --pull: depodaki .npz/.kal/işaret dosyalarını indirir; dl_prepare.py bunları "var" sayar ve atlar
    (önceki oturumda kalınan yerden devam).
  * --push: tamamlanmış videoların kalitesini hesaplar (dl_quality.compute, .kal) ve .npz + .npy + .kal dosyalarını
    toplu commit'lerle yükler. Yüklenen .npy yerelde silinir (disk); .yuklendi işareti bırakılır.
    --loop N ile N saniyede bir, --until-pid süreci bitene kadar çalışır, sonra son bir kez yükler.
  * --download: eğitim oturumunda verinin tamamını (kareler dahil) indirir.

Anahtarlar: okuma HF_TOKEN, yazma HF_WRITE_TOKEN (Kaggle Secrets). Depo: <kullanıcı>/rppg-veri (gizli).

    python scripts/dl_hf_sync.py --data /tmp/dl --subs mmpd test_mmpd vipl test_vipl --pull
    python scripts/dl_hf_sync.py --data /tmp/dl --subs mmpd test_mmpd vipl test_vipl --push --loop 900 --until-pid 123
"""
import argparse
import glob
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO_NAME = "rppg-veri"
MARKS = ("*.npz", "*.kal", "*.kizilotesi")  # küçük dosyalar: "bu video işlendi" bilgisi
DONE = ".yuklendi"
BATCH_BYTES = 1.5e9  # commit başına en çok ~1.5 GB


def repo_id(api):
    return f"{api.whoami()['name']}/{REPO_NAME}"


def _api(write):
    # Kendi gizli depomuz: okuma anahtarında "kendi depolarını oku" izni olmayabilir, yazma anahtarı önce denenir
    tok = os.environ.get("HF_WRITE_TOKEN") or (None if write else os.environ.get("HF_TOKEN"))
    if not tok:
        sys.exit(("HF_WRITE_TOKEN" if write else "HF_TOKEN") + " yok (Kaggle: Add-ons -> Secrets)")
    from huggingface_hub import HfApi
    return HfApi(token=tok)


def pull(api, repo, data, subs, full=False):
    """Depodaki işaret dosyalarını (full: kareler dahil her şeyi) data/ altına indirir."""
    from huggingface_hub import snapshot_download
    if not api.repo_exists(repo, repo_type="dataset"):
        print(f"{repo} henüz yok; sıfırdan başlanıyor", flush=True)
        return
    pats = [f"{s}/*" for s in subs] if full else [f"{s}/{m}" for s in subs for m in MARKS]
    snapshot_download(repo, repo_type="dataset", local_dir=data, allow_patterns=pats, token=api.token,
                      max_workers=8)
    for s in subs:
        d = os.path.join(data, s)
        n = len(glob.glob(os.path.join(d, "*.npz")))
        for p in glob.glob(os.path.join(d, "*.kal")):
            os.utime(p)  # indirme sırası rastgele: .kal, .npz'den eski görünüp yeniden hesaplanmasın (kareler yok)
        if not full:  # indirilenler zaten depoda: tekrar yüklenmesin
            for p in glob.glob(os.path.join(d, "*.npz")):
                open(p[:-4] + DONE, "w").close()
            for p in glob.glob(os.path.join(d, "*.kizilotesi")):
                open(p + DONE, "w").close()
        print(f"  {s}: {n} video depoda", flush=True)


def pending(data, subs):
    """Tamamlanmış (npz yazılmış) ama yüklenmemiş videolar. npz en son yazılır: varsa npy de tamdır."""
    out = []
    for s in subs:
        for p in sorted(glob.glob(os.path.join(data, s, "*.npz"))):
            if not os.path.exists(p[:-4] + DONE):
                out.append(p)
    return out


def _files_of(npz):
    base = npz[:-4]
    return [f for f in (npz, base + ".npy", base + ".kal", npz + ".kizilotesi") if os.path.exists(f)]


def push(api, repo, data, subs, quality=True):
    """Bekleyen videoları toplu commit'lerle yükler; yüklenen .npy silinir. Yüklenen video sayısını döndürür."""
    from huggingface_hub import CommitOperationAdd
    marks = [p for s in subs for p in glob.glob(os.path.join(data, s, "*.kizilotesi"))
             if not os.path.exists(p + DONE)]
    todo = pending(data, subs)
    if not todo and not marks:
        return 0
    if quality:
        from dl_quality import compute
        for p in todo:
            try:
                compute(p)  # .npy yoksa (yüz bulunamadı, kare saklanmadı) None döner
            except Exception as e:  # noqa: BLE001  bozuk dosya yüklemeyi durdurmasın
                print(f"  kalite hatası {os.path.basename(p)}: {e!r}", flush=True)
    api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
    groups, cur, size = [], [], 0.0
    for p in todo:
        fs = _files_of(p)
        sz = sum(os.path.getsize(f) for f in fs)
        if cur and size + sz > BATCH_BYTES:
            groups.append(cur)
            cur, size = [], 0.0
        cur.append(p)
        size += sz
    if cur or marks:
        groups.append(cur)
    done = 0
    for i, g in enumerate(groups):
        files = [f for p in g for f in _files_of(p)] + (marks if i == 0 else [])
        ops = [CommitOperationAdd(path_in_repo=os.path.relpath(f, data).replace(os.sep, "/"), path_or_fileobj=f)
               for f in files]
        api.create_commit(repo, operations=ops, repo_type="dataset",
                          commit_message=f"{len(g)} video ({', '.join(subs)})")
        for p in g:
            npy = p[:-4] + ".npy"
            if os.path.exists(npy):
                os.remove(npy)
            open(p[:-4] + DONE, "w").close()
        if i == 0:
            for m in marks:
                open(m + DONE, "w").close()
        done += len(g)
        print(f"  yüklendi {done}/{len(todo)} video", flush=True)
    return done


def _alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # Linux: bitmiş ama beklenmemiş alt süreç (zombi) canlı sayılmasın
        with open(f"/proc/{pid}/stat") as f:
            return f.read().split(")")[-1].split()[0] != "Z"
    except OSError:
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/tmp/dl")
    ap.add_argument("--subs", nargs="+", required=True, help="alt klasörler, ör. mmpd test_mmpd vipl test_vipl")
    ap.add_argument("--pull", action="store_true", help="işaret dosyalarını indir (kalınan yerden devam)")
    ap.add_argument("--push", action="store_true", help="bekleyen videoları yükle")
    ap.add_argument("--download", action="store_true", help="eğitim için her şeyi indir")
    ap.add_argument("--loop", type=int, default=0, help="--push: kaç saniyede bir")
    ap.add_argument("--until-pid", type=int, default=0, help="--loop: bu süreç bitince son kez yükle ve çık")
    a = ap.parse_args()

    api = _api(write=a.push)
    repo = repo_id(api)
    if a.pull or a.download:
        pull(api, repo, a.data, a.subs, full=a.download)
    if a.push:
        while True:
            finished = a.until_pid and not _alive(a.until_pid)
            try:
                n = push(api, repo, a.data, a.subs)
                if n:
                    print(f"{time.strftime('%H:%M')} {n} video yüklendi -> huggingface.co/datasets/{repo}", flush=True)
            except Exception as e:  # noqa: BLE001  ağ hatası: sonraki turda tekrar dene
                print(f"{time.strftime('%H:%M')} yükleme hatası: {e!r}", flush=True)
                if finished or not a.loop:
                    sys.exit(1)
            if finished or not a.loop:
                break
            time.sleep(a.loop)


if __name__ == "__main__":
    main()
