"""Tool a disposizione dell'agente, costruiti per un singolo owner."""

from datetime import datetime

from langchain_core.tools import tool

from src.config import NOTES_DIR
from src.retrieval import get_retriever, list_source_files
from src.tenancy import validate_owner_id


def build_tools(owner_id: str) -> list:
    owner_id = validate_owner_id(owner_id)

    @tool
    def search_course_material(query: str) -> str:
        """Cerca nel materiale del corso di Intelligenza Artificiale.
        Usalo per qualsiasi domanda sui contenuti del corso. Puoi chiamarlo piu' volte
        con query diverse se ti servono informazioni su argomenti distinti.
        Restituisce estratti con file di origine e numero di pagina."""
        docs = get_retriever(owner_id).invoke(query)
        if not docs:
            return "Nessun risultato trovato."
        return "\n\n".join(
            f"[{d.metadata.get('source_file')} p.{d.metadata.get('page_label')}]\n{d.page_content}"
            for d in docs
        )

    @tool
    def list_course_documents() -> str:
        """Elenca i documenti del corso disponibili. Usalo quando l'utente chiede
        quali argomenti o materiali sono presenti."""
        files = list_source_files(owner_id)
        return "\n".join(files) if files else "Nessun documento disponibile."

    @tool
    def save_study_note(title: str, content: str) -> str:
        """Salva un appunto di studio in formato markdown. Usalo SOLO quando l'utente
        chiede esplicitamente di salvare, annotare o creare un riassunto da conservare."""
        notes_dir = NOTES_DIR / owner_id
        notes_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
        path = notes_dir / f"{datetime.now():%Y%m%d_%H%M}_{safe}.md"
        path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
        return f"Appunto salvato in {path}"

    return [search_course_material, list_course_documents, save_study_note]
