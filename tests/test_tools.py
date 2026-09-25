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


def test_build_tools_rejects_invalid_owner():
    with pytest.raises(ValueError):
        build_tools("../bob")
