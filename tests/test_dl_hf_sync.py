"""dl_hf_sync: yükleme mantığı (HF'e bağlanmadan, sahte API ile)."""
import os
import sys
import types

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import dl_hf_sync as sync  # noqa: E402


class FakeApi:
    def __init__(self):
        self.commits = []

    def create_repo(self, *a, **k):
        pass

    def create_commit(self, repo, operations, **k):
        self.commits.append([op.path_in_repo for op in operations])


@pytest.fixture(autouse=True)
def fake_hub(monkeypatch):
    mod = types.ModuleType("huggingface_hub")
    mod.CommitOperationAdd = lambda path_in_repo, path_or_fileobj: types.SimpleNamespace(path_in_repo=path_in_repo)
    monkeypatch.setitem(sys.modules, "huggingface_hub", mod)


def _video(d, name, frames=True):
    os.makedirs(d, exist_ok=True)
    if frames:
        np.save(os.path.join(d, name + ".npy"), np.zeros((4, 72, 72, 3), np.uint8))
    np.savez(os.path.join(d, name + ".npz"), bvp=np.zeros(4))


def test_push_uploads_once_and_frees_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "BATCH_BYTES", 1)  # her video ayrı commit
    d = tmp_path / "mmpd"
    _video(str(d), "a")
    _video(str(d), "b", frames=False)  # yüz bulunamadı: yalnızca etiket dosyası
    (d / "c.npz.kizilotesi").write_text("")
    api = FakeApi()
    assert sync.push(api, "u/r", str(tmp_path), ["mmpd"], quality=False) == 2
    paths = sorted(p for c in api.commits for p in c)
    assert paths == ["mmpd/a.npy", "mmpd/a.npz", "mmpd/b.npz", "mmpd/c.npz.kizilotesi"]
    assert not (d / "a.npy").exists()  # yüklenen kareler silindi
    assert (d / "a.npz").exists()      # dl_prepare atlasın diye etiket dosyası kalır
    assert sync.push(api, "u/r", str(tmp_path), ["mmpd"], quality=False) == 0
    assert len(api.commits) == 2


def test_failed_commit_keeps_files(tmp_path):
    _video(str(tmp_path / "vipl"), "a")

    class Broken(FakeApi):
        def create_commit(self, *a, **k):
            raise ConnectionError("ağ")

    with pytest.raises(ConnectionError):
        sync.push(Broken(), "u/r", str(tmp_path), ["vipl"], quality=False)
    assert (tmp_path / "vipl" / "a.npy").exists()
    assert sync.pending(str(tmp_path), ["vipl"]) == [str(tmp_path / "vipl" / "a.npz")]
