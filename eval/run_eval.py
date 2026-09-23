import json
from pathlib import Path
from src.retrieval import get_retriever


KS = [1,3,5,10]

def first_hit_rank(docs,expected_file, expected_pages):
    for rank, doc in enumerate(docs, start = 1):
        if (doc.metadata.get("source_file") == expected_file and doc.metadata.get("page_label") in expected_pages):
            return rank
    return None

def main():
    dataset = json.loads((Path(__file__).parent / "dataset.json").read_text(encoding= "utf-8"))
    retriever = get_retriever(k = max(KS))  #recupero 10 una volta sola

    ranks = []
    for item in dataset:
        docs = retriever.invoke(item["question"])
        rank = first_hit_rank(docs,item["expected_file"],item["expected_pages"])
        ranks.append(rank)

        # le domande fuori dai primi 3 (il k di produzione) sono quelle da studiare
        if rank is None or rank > 3:
            print(f"\n[rank={rank}] {item['question']}")
            print(f"  atteso: {item['expected_file']} p.{item['expected_pages']}")
            for doc in docs[:3]:
                print(f"  preso:  {doc.metadata.get('source_file')} p.{doc.metadata.get('page_label')}")

    print(f"\n{'k':>3} | {'hit-rate':>8} | {'MRR':>5}")
    for k in KS:
        hits = [r for r in ranks if r is not None and r <=k ]
        hit_rate = len(hits)/len(ranks)
        mrr = sum(1 / r for r in hits) / len(ranks)
        print(f"{k:>3} | {hit_rate:>8.2f} | {mrr:>5.2f}")


if __name__ == "__main__":
    main()
