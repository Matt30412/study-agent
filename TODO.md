# Fase 0 — cosa resta da fare

Checklist di lavoro per completare la fase 0 della roadmap (vedi [README.md](README.md)).
Ordine consigliato: `config.py` → eval set → test. La config va per prima perché
l'eval la importerà.

---

## Dati che ti servono (già verificati, non ricontrollarli)

Struttura del payload in Qdrant:

```
payload
├── page_content
└── metadata
    ├── source_file    # es. "3_RcercaNonInformata.pdf"
    ├── page           # 0-indexed  → 13
    ├── page_label     # 1-indexed  → "14"   (stringa)
    ├── total_pages
    └── source, producer, creator, creationdate, moddate
```

⚠️ **`page` è 0-indexed, `page_label` no.** Se apri il PDF e leggi "pagina 14", nei
metadata trovi `page=13` e `page_label="14"`. Nell'eval set usa **`page_label`**:
scrivendo 30 voci a mano, confrontare con `page` significa sbagliare tutto di uno e
passare la serata a debuggare l'eval invece del retrieval.

---

## 1. `src/config.py`

Circa 15 minuti, meccanico.

- [ ] Creare `src/config.py`
- [ ] Spostarci `QDRANT_URL`, `COLLECTION_NAME`, `EMBEDDING_MODEL`
      (oggi duplicati in `ingestion.py` **e** `retrieval.py`)
- [ ] Spostarci `LLM_MODEL` da `agents.py`
- [ ] Spostarci `CHUNK_SIZE = 800`, `CHUNK_OVERLAP = 100`, `RETRIEVER_K = 3`
- [ ] `DATA_DIR` e `NOTES_DIR` **ancorati al file**, non al cwd:
      `Path(__file__).resolve().parent.parent / "data"`
- [ ] Aggiornare i quattro moduli perché importino da lì
- [ ] Verificare che `python -m src.app` parta ancora

**Da NON spostare:** `SYSTEM_PROMPT`, `ROUTER_PROMPT`, `REFUSAL`. Sono logica
dell'agente, non configurazione — se finiscono in `config.py`, per capire cosa fa il
router devi aprire due file.

**Opzionale:** `pydantic-settings` al posto delle costanti semplici, così `QDRANT_URL`
può arrivare da variabile d'ambiente con un default. Servirà comunque in fase 2, ma va
benissimo anche partire da costanti e migrare dopo.

✅ **Fatto quando:** nessuna costante di configurazione compare più di una volta nel
progetto, e l'app si lancia da una directory qualsiasi.

---

## 2. Eval set del retrieval

È il pezzo che conta. Senza, ogni scelta successiva della roadmap è un'opinione.

**Struttura:** `eval/dataset.json` (i dati) + `eval/run_eval.py` (le metriche).

**Formato di ogni voce:**

```json
{
  "question": "...",
  "expected_file": "3_RcercaNonInformata.pdf",
  "expected_pages": ["13", "14"]
}
```

`expected_pages` è una lista perché un concetto sta spesso a cavallo di due slide.
Sono stringhe perché `page_label` è una stringa.

### Come scrivere le domande

- [ ] 25-30 domande, tutte con pagina attesa verificata aprendo il PDF

Due regole, entrambe importanti:

1. **Non scriverle a memoria.** Apri il PDF, scegli un concetto, annota la pagina, e
   *poi* scrivi la domanda come la porrebbe uno studente — con parole sue, non con
   quelle della slide. Se ricopi il titolo della slide, l'embedding trova il chunk per
   costruzione e la metrica ti mente.

2. **Includi domande che ti aspetti falliscano.** Sinonimi che il corso non usa,
   concetti spalmati su più pagine, e soprattutto il caso noto: **la query su
   best-first**, che oggi manca il chunk giusto anche se il materiale c'è
   (`3_RcercaNonInformata.pdf`, dove la ricerca in ampiezza è presentata come
   best-first con `f(n)` = profondità). Un eval set dove passa tutto non misura la
   qualità del retrieval, misura che hai scelto domande facili.

### Le metriche

- [ ] Implementare `hit-rate@k` e `MRR@k`
- [ ] Stampare i risultati per `k in [1, 3, 5, 10]`

Definizione di **hit**: un chunk fra i primi k con `source_file == expected_file`
**e** `page_label ∈ expected_pages`.

| Metrica | Formula | Risponde a |
|---|---|---|
| hit-rate@k | frazione di domande con ≥ 1 hit nei primi k | "il materiale giusto è arrivato?" |
| MRR@k | media di `1/rango` del **primo** hit (rango 1-indexed, 0 se nessun hit) | "è arrivato in cima o in fondo?" |

Servono entrambe. Un hit-rate di 1.0 con MRR 0.3 significa che il chunk giusto c'è
sempre ma è sempre quarto — e con `RETRIEVER_K=3` in produzione non lo vedresti mai.
La curva su k è il modo per scoprire se 3 è il valore giusto.

### Vincolo: niente LLM nell'eval

- [ ] Chiamare direttamente il retriever, **non** l'agente

Si misura *solo* il retrieval. Così gira in secondi invece che in minuti, è
deterministico, e isola la variabile: se domani cambi modello generativo (fase 7,
Bedrock) questi numeri non devono muoversi di un millimetro. La valutazione end-to-end
della qualità delle risposte è un'altra cosa e viene dopo.

✅ **Fatto quando:** `python -m eval.run_eval` stampa una tabella hit-rate/MRR per i
quattro valori di k, e i numeri sono scritti nel README.

---

## 3. Test

- [ ] `test_router_refuses` — llm mockato restituisce `"FUORI_TEMA"` → `route == "refuse"`
- [ ] `test_router_fail_open` — llm mockato restituisce spazzatura → `route == "agent"`
- [ ] `test_note_filename` — titolo con `/`, `..`, emoji → filename sicuro
- [ ] `test_chunking` — testo noto → numero di chunk e overlap attesi

Il secondo è il più importante: è l'unico che protegge la scelta del fail-open, che
altrimenti a chi legge il codice sembra un bug.

### Il problema che incontrerai (è voluto)

`router` è una closure dentro `build_agent()`, quindi non è importabile e non è
testabile. Due strade:

1. monkeypatchare `ChatOllama`
2. estrarre la classificazione in una funzione a livello di modulo, tipo
   `classify_question(llm, messages) -> str`, che `build_agent` poi usa

**Prendi la seconda.** Quando un test è difficile da scrivere, quasi sempre è il
design che sta segnalando qualcosa: quella logica non ha motivo di stare sepolta in
una closure.

✅ **Fatto quando:** `uv run pytest` passa senza che Qdrant o Ollama siano accesi.

---

## Chiudendo la fase 0

- [ ] Aggiornare le checkbox della fase 0 nel README
- [ ] Scrivere i numeri dell'eval nel README (è il contenuto più interessante del repo)
- [ ] Commit

Poi si parte con la **fase 1 — multi-tenancy nel codice**.
