"""
ELK Performance Benchmark Suite
Measures key performance metrics for optimization tracking.

Usage:
    python tests/benchmark.py              # Quick test
    pytest tests/benchmark.py -v           # Full benchmark
    pytest tests/benchmark.py --benchmark  # With pytest-benchmark
"""

import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""
    name: str
    duration_ms: float
    iterations: int
    avg_ms: float
    min_ms: float
    max_ms: float
    

def measure(func, iterations: int = 5, warmup: int = 1, name: str = "") -> BenchmarkResult:
    """Measure function execution time."""
    # Warmup
    for _ in range(warmup):
        func()
    
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    return BenchmarkResult(
        name=name or func.__name__,
        duration_ms=sum(times),
        iterations=iterations,
        avg_ms=sum(times) / len(times),
        min_ms=min(times),
        max_ms=max(times)
    )


class ELKBenchmark:
    """Benchmark suite for ELK components."""
    
    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
    
    def benchmark_json_parsing(self) -> BenchmarkResult:
        """B1: JSON parsing with orjson vs stdlib."""
        from elk.kernel.ai.llm import json_loads
        
        # Sample LLM response
        sample = json.dumps({
            "incident_type": "FIRE",
            "urgency": "HIGH",
            "location": {"details": "Quartier Seghir, près de la mosquée"},
            "victims_count": 2,
            "confidence": 0.85
        })
        
        result = measure(
            lambda: json_loads(sample),
            iterations=1000,
            name="JSON Parsing (orjson)"
        )
        self.results["json_parsing"] = result
        return result
    
    def benchmark_rag_keyword_search(self) -> BenchmarkResult:
        """B2: RAG keyword search with caching."""
        from elk.kernel.rag.vector_store import HybridRAG
        
        # Setup RAG with sample knowledge
        rag = HybridRAG(vector_store=None)
        rag.load_pack_knowledge(
            communes=["akbou", "sidi aich", "amizour", "tichy", "aokas"],
            quartiers=["seghir", "ihaddaden", "sidi ahmed", "edimco"],
            vocab={"lfeu": "feu", "laccident": "accident", "lvictime": "victime"}
        )
        
        sample_text = "yella lfeu g akbou, quartier seghir"
        
        # First call (cold)
        cold_result = measure(
            lambda: rag.keyword_search(sample_text),
            iterations=1,
            name="RAG Keyword (cold)"
        )
        
        # Cached calls
        cached_result = measure(
            lambda: rag.keyword_search(sample_text),
            iterations=100,
            name="RAG Keyword (cached)"
        )
        
        self.results["rag_cold"] = cold_result
        self.results["rag_cached"] = cached_result
        return cached_result
    
    def benchmark_confidence_calculation(self) -> BenchmarkResult:
        """B3: Confidence calculator speed."""
        from elk.kernel.scoring import ConfidenceCalculator
        
        calc = ConfidenceCalculator()
        
        sample_transcription = "yella lfeu g akbou, quartier seghir, urgent"
        sample_extracted = {
            "incident_type": "FIRE",
            "urgency": "HIGH", 
            "location": {"details": "Akbou quartier seghir"}
        }
        sample_context = "DETECTED_LOCATION: Akbou (Commune de Bejaia)"
        
        result = measure(
            lambda: calc.calculate(sample_transcription, sample_extracted, sample_context),
            iterations=100,
            name="Confidence Calculation"
        )
        self.results["confidence"] = result
        return result
    
    def benchmark_model_registry(self) -> BenchmarkResult:
        """A1: ModelRegistry singleton access."""
        from elk.kernel.models import get_model_registry
        
        # Measure singleton access speed
        result = measure(
            lambda: get_model_registry(),
            iterations=1000,
            name="ModelRegistry Access"
        )
        self.results["registry_access"] = result
        return result
    
    def benchmark_transcription_cache(self) -> BenchmarkResult:
        """A2: TranscriptionCache hit vs miss."""
        from elk.kernel.models import get_transcription_cache
        import tempfile
        import os
        
        cache = get_transcription_cache()
        cache.clear()
        
        # Create a temp file for testing
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 1024)  # Fake WAV header
            temp_path = f.name
        
        try:
            # Miss (first access)
            miss_result = measure(
                lambda: cache.get(temp_path),
                iterations=100,
                name="TranscriptionCache (miss)"
            )
            
            # Populate cache
            cache.set(temp_path, "test transcription")
            
            # Hit (cached)
            hit_result = measure(
                lambda: cache.get(temp_path),
                iterations=100,
                name="TranscriptionCache (hit)"
            )
            
            self.results["cache_miss"] = miss_result
            self.results["cache_hit"] = hit_result
            
            return hit_result
        finally:
            os.unlink(temp_path)
            cache.clear()
    
    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks."""
        print("=" * 60)
        print("⚡ ELK Performance Benchmark Suite")
        print("=" * 60)
        
        benchmarks = [
            ("JSON Parsing", self.benchmark_json_parsing),
            ("RAG Keyword Search", self.benchmark_rag_keyword_search),
            ("Confidence Calc", self.benchmark_confidence_calculation),
            ("ModelRegistry", self.benchmark_model_registry),
            ("TranscriptionCache", self.benchmark_transcription_cache),
        ]
        
        for name, bench_func in benchmarks:
            try:
                result = bench_func()
                print(f"\n✅ {name}")
                print(f"   Avg: {result.avg_ms:.3f}ms | Min: {result.min_ms:.3f}ms | Max: {result.max_ms:.3f}ms")
            except Exception as e:
                print(f"\n❌ {name}: {e}")
        
        print("\n" + "=" * 60)
        print("📊 Summary")
        print("=" * 60)
        
        for name, result in self.results.items():
            print(f"  {name}: {result.avg_ms:.3f}ms avg ({result.iterations} iterations)")
        
        return self.results
    
    def save_results(self, path: str = "benchmark_results.json"):
        """Save results to JSON for comparison."""
        import datetime
        
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "results": {k: asdict(v) for k, v in self.results.items()}
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📁 Results saved to: {path}")


def main():
    """Run benchmarks from command line."""
    benchmark = ELKBenchmark()
    benchmark.run_all()
    benchmark.save_results()


if __name__ == "__main__":
    main()
