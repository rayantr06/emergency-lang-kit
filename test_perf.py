import time
import timeit
from elk.engine.rag.vector_store import HybridRAG

def test_performance():
    rag = HybridRAG()

    # Generate some dummy data
    communes = [f"commune_{i}" for i in range(1000)]
    quartiers = [f"quartier_{i}" for i in range(1000)]
    vocab = {f"word_{i}": f"mot_{i}" for i in range(1000)}

    rag.load_pack_knowledge(communes, quartiers, vocab)

    # Benchmark keyword search
    def run_search():
        rag.keyword_search("commune_500 and quartier_500 with word_500")

    # Run benchmark
    number = 100000
    time_taken = timeit.timeit(run_search, number=number)

    print(f"Time for {number} iterations: {time_taken:.4f} seconds")

if __name__ == "__main__":
    test_performance()
