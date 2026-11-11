"""Telefon A/B ölçümlerinin model kimliğini kaybetmeden okunması."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eval_app_csv import read_refs, summary


def test_model_column_survives_second_table(tmp_path):
    p = tmp_path / "session.csv"
    p.write_text("zaman_s,nabiz_bpm,model\n10,72,pure\n\n"
                 "zaman,tur,kamera,uygulama_bpm,cihaz_bpm,fark,guvenilir,snr_db,model\n"
                 "now,kayit,on,72,74,-2,1,4,pure\n", encoding="utf-8")
    table = read_refs(str(p))
    assert list(table.model) == ["pure"]
    assert summary(table)["MAE"] == 2


def test_legacy_csv_is_marked_without_guessing_model(tmp_path):
    p = tmp_path / "old.csv"
    p.write_text("zaman,tur,kamera,uygulama_bpm,cihaz_bpm,fark,guvenilir,snr_db\n"
                 "now,kayit,on,72,74,-2,1,4\n", encoding="utf-8")
    assert list(read_refs(str(p)).model) == ["eski_kayit"]
