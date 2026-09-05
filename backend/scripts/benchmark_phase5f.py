"""
SIF Sentinel — Phase 5F Performance Benchmark Suite

Executes rigorous timing benchmarks across:
1. Single-barrier recommendation generation
2. Multi-barrier counterfactual trajectory calculation
3. End-to-end intervention intelligence pipeline
"""

import time
import statistics
import numpy as np

from app.services.analysis.analysis_service import AnalysisService
from app.services.nlp.causal_engine import ControlStatus
from app.services.nlp.counterfactual_engine import CounterfactualSafetyEngine
from app.services.nlp.intervention_engine import SafetyInterventionEngine

BENCHMARK_INCIDENT = (
    "Worker entered nitrogen purge vessel without atmospheric gas testing or entry permit."
)

def run_benchmarks(iterations: int = 100):
    print(f"Starting Phase 5F Benchmarking ({iterations} iterations)...")

    # Warmup
    analysis = AnalysisService(None).analyze_direct(BENCHMARK_INCIDENT)
    graph = analysis.safety_graph

    # 1. Benchmark: Single-Barrier Counterfactual Simulation
    single_barrier_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        CounterfactualSafetyEngine.simulate_barrier_restoration(
            original_graph=graph,
            target_control="Gas Testing",
            simulated_status=ControlStatus.VERIFIED,
            original_risk_score=95,
        )
        t1 = time.perf_counter()
        single_barrier_times.append((t1 - t0) * 1000.0)

    # 2. Benchmark: Multi-Barrier Trajectory Simulation
    multi_barrier_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        CounterfactualSafetyEngine.simulate_multi_barrier_restoration(
            original_graph=graph,
            target_controls=[
                ("Gas Testing", ControlStatus.VERIFIED),
                ("Entry Permit", ControlStatus.VERIFIED),
            ],
            original_risk_score=95,
        )
        t1 = time.perf_counter()
        multi_barrier_times.append((t1 - t0) * 1000.0)

    # 3. Benchmark: Intervention Recommendation & Cumulative Plan Engine
    intervention_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        SafetyInterventionEngine.generate_interventions(
            safety_graph=graph,
            risk_score=95,
            risk_priority="CRITICAL",
            life_saving_rule="Confined Space Entry",
            sif_level="PSIF",
        )
        t1 = time.perf_counter()
        intervention_times.append((t1 - t0) * 1000.0)

    def print_metrics(name: str, times: list[float]):
        mean_v = statistics.mean(times)
        p50 = float(np.percentile(times, 50))
        p95 = float(np.percentile(times, 95))
        p99 = float(np.percentile(times, 99))
        print(f"\n[{name}]")
        print(f"  Mean: {mean_v:.3f} ms")
        print(f"  P50 : {p50:.3f} ms")
        print(f"  P95 : {p95:.3f} ms")
        print(f"  P99 : {p99:.3f} ms")

    print_metrics("Single-Barrier Counterfactual Simulation", single_barrier_times)
    print_metrics("Multi-Barrier Sequential Trajectory", multi_barrier_times)
    print_metrics("Phase 5F Intervention Intelligence & Plan Generation", intervention_times)


if __name__ == "__main__":
    run_benchmarks(200)
