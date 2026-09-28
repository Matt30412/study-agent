from itertools import pairwise

from pypdf import PdfWriter

from src.config import CHUNK_SIZE
from src.ingestion import SPLITTER, load_pdf


def test_load_pdf_page_numbers(tmp_path):
    # L'eval set confronta page_label, che parte da 1 ed è una stringa: page parte da 0.
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=100, height=100)
    path = tmp_path / "slide.pdf"
    writer.write(path)

    pages = load_pdf(path)

    assert [p.metadata["page"] for p in pages] == [0, 1, 2]
    assert [p.metadata["page_label"] for p in pages] == ["1", "2", "3"]
    assert {p.metadata["source_file"] for p in pages} == {"slide.pdf"}


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"parola{i:03d}" for i in range(400))

    chunks = SPLITTER.split_text(text)

    assert len(chunks) > 1
    assert all(len(c) <= CHUNK_SIZE for c in chunks)
    # Ogni chunk riparte dalla coda del precedente: un concetto a cavallo del taglio non si perde.
    for prev, nxt in pairwise(chunks):
        assert nxt.split()[0] in prev.split()


def test_paragraphs_are_not_split():
    # Due paragrafi che insieme superano CHUNK_SIZE: il taglio cade fra i due, non a metà frase.
    first = "La ricerca in ampiezza espande i nodi un livello alla volta. " * 7
    second = "La ricerca in profondita' espande sempre il nodo piu' profondo. " * 7

    assert SPLITTER.split_text(f"{first}\n\n{second}") == [first.strip(), second.strip()]
