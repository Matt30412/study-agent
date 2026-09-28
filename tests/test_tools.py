import pytest

from src.tools import build_tools


def test_owner_not_in_tool_schema():
    # Regola di sicurezza del README: se owner_id fosse un argomento, lo sceglierebbe l'LLM.
    for t in build_tools("alice"):
        assert "owner_id" not in t.args


def test_notes_saved_under_owner(tmp_path, monkeypatch):
    monkeypatch.setattr("src.tools.NOTES_DIR", tmp_path)
    save = {t.name: t for t in build_tools("alice")}["save_study_note"]

    save.invoke({"title": "prova", "content": "testo"})

    assert len(list((tmp_path / "alice").glob("*.md"))) == 1
    assert not list(tmp_path.glob("*.md"))


@pytest.mark.parametrize(
    "title", ["../../etc/passwd", "a/b\\c", "C:\\Windows", "BFS 🧠", "x" * 200]
)
def test_note_filename_is_safe(tmp_path, monkeypatch, title):
    # Il titolo lo sceglie l'LLM: non deve poter uscire dalla cartella dell'owner.
    monkeypatch.setattr("src.tools.NOTES_DIR", tmp_path)
    save = {t.name: t for t in build_tools("alice")}["save_study_note"]

    result = save.invoke({"title": title, "content": "testo"})

    [note] = (tmp_path / "alice").iterdir()
    assert all(c.isalnum() or c in "-_" for c in note.stem)
    assert len(note.stem) <= len("20260101_1200_") + 60
    assert str(tmp_path) not in result  # nessun percorso del server nella risposta


def test_build_tools_rejects_invalid_owner():
    with pytest.raises(ValueError):
        build_tools("../bob")
