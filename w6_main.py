"""
w6_main.py
~~~~~~~~~~
W6 异步基础设施全链路合体压测与 Benchmark 产出脚本
"""

import asyncio
import os
import time
from typing import List, Tuple
import httpx
import psutil

from async_core import AsyncTokenBucket, async_retry, bounded_worker_pool

MOCK_URL = "http://127.0.0.1:9000/delay"
proc = psutil.Process(os.getpid())

def get_memory_mb() -> float:
    return proc.memory_info().rss / (1024 * 1024)

def calculate_percentiles(latencies: List[float]) -> Tuple[float, float, float]:
    """计算 P50 / P95 / P99 毫秒分位数"""
    if not latencies:
        return 0.0, 0.0, 0.0
    s = sorted(latencies)
    n = len(s)
    p50 = s[int(n * 0.50)] * 1000
    p95 = s[min(int(n * 0.95), n - 1)] * 1000
    p99 = s[min(int(n * 0.99), n - 1)] * 1000
    return p50, p95, p99

async def run_benchmark_case(
    total_requests: int,
    max_connections: int,
    concurrency_limit: int,
    rate_limit_qps: float = 100.0,
) -> Tuple[float, float, float, float, float]:
    """执行单个压测组合：返回 (P50, P95, P99, QPS, 耗时秒)"""
    bucket = AsyncTokenBucket(rate=rate_limit_qps, capacity=concurrency_limit)
    latencies: List[float] = []
    latencies_lock = asyncio.Lock()

    # 初始化配置物理连接池大小的 httpx 客户端
    limits = httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_connections)
    async with httpx.AsyncClient(limits=limits, timeout=5.0) as client:

        # 1. 组装：@async_retry 保护单次请求
        @async_retry(max_retries=3, base_delay=0.05, factor=2.0, retry_on=(httpx.HTTPError,))
        async def fetch_one(req_id: int):
            # 2. 组装：穿过令牌桶限流门禁
            async with bucket:
                t0 = time.perf_counter()
                resp = await client.get(MOCK_URL)
                resp.raise_for_status()
                cost = time.perf_counter() - t0
                async with latencies_lock:
                    latencies.append(cost)
                return req_id

        # 3. 组装：使用 bounded_worker_pool 执行有界真背压并发
        t_start = time.perf_counter()
        await bounded_worker_pool(
            items=range(total_requests),
            handler=fetch_one,
            concurrency=concurrency_limit,
            queue_size=concurrency_limit * 2,
            return_exceptions=False,
        )
        total_time = time.perf_counter() - t_start

    p50, p95, p99 = calculate_percentiles(latencies)
    qps = len(latencies) / total_time
    return p50, p95, p99, qps, total_time

async def run_memory_comparison(total: int = 300, concurrency: int = 10):
    print("\n" + "=" * 65)
    print(" 📊 对照实验一：无背压 (gather) vs 有背压 (bounded_worker_pool) 内存对比")
    print("=" * 65)

    # 方式 A: gather + Semaphore (无背压)
    sem = asyncio.Semaphore(concurrency)
    async def worker_a(i):
        async with sem:
            await asyncio.sleep(0.01)

    mem_before_a = get_memory_mb()
    coros = [worker_a(i) for i in range(total)]
    mem_peak_a = get_memory_mb()
    await asyncio.gather(*coros)
    print(f" • 方式 1 [gather + Semaphore({concurrency})]: 峰值 RSS = {mem_peak_a:.2f} MB")

    # 方式 B: bounded_worker_pool (真背压)
    async def worker_b(i):
        await asyncio.sleep(0.01)

    mem_before_b = get_memory_mb()
    await bounded_worker_pool(range(total), worker_b, concurrency=concurrency, queue_size=20)
    mem_peak_b = get_memory_mb()
    print(f" • 方式 2 [bounded_worker_pool(c={concurrency}, q=20)]: 峰值 RSS = {mem_peak_b:.2f} MB")

    return mem_peak_a, mem_peak_b

async def main():
    print("=" * 65)
    print(" 🚀 W6 异步基础设施全链路合体压测 (300 请求实战)")
    print("=" * 65)

    TOTAL = 300

    # 实验 1: 连接池 10, 信号量/并发 100
    print(f"--> [组合 1] 运行 {TOTAL} 个请求 (连接池=10, 信号量=100)...")
    p50_1, p95_1, p99_1, qps_1, t1 = await run_benchmark_case(TOTAL, max_connections=10, concurrency_limit=100)
    print(f"    完成！耗时: {t1:.2f}s | QPS: {qps_1:.1f} | P50: {p50_1:.1f}ms | P95: {p95_1:.1f}ms | P99: {p99_1:.1f}ms\n")

    # 实验 2: 连接池 50, 信号量/并发 50
    print(f"--> [组合 2] 运行 {TOTAL} 个请求 (连接池=50, 信号量=50)...")
    p50_2, p95_2, p99_2, qps_2, t2 = await run_benchmark_case(TOTAL, max_connections=50, concurrency_limit=50)
    print(f"    完成！耗时: {t2:.2f}s | QPS: {qps_2:.1f} | P50: {p50_2:.1f}ms | P95: {p95_2:.1f}ms | P99: {p99_2:.1f}ms")

    # 内存对照
    mem_a, mem_b = await run_memory_comparison(total=TOTAL, concurrency=10)

    print("\n" + "=" * 65)
    print(" 📋 请将以下真实测得的数据记录进 docs/async_benchmark.md：")
    print("=" * 65)
    print(f"""
## 压测（300 请求）

| 连接池 | 信号量 | P50 | P95 | P99 | QPS |
|---|---|---|---|---|---|
| 10 | 100 | {p50_1:.1f}ms | {p95_1:.1f}ms | {p99_1:.1f}ms | {qps_1:.1f} |
| 50 | 50  | {p50_2:.1f}ms | {p95_2:.1f}ms | {p99_2:.1f}ms | {qps_2:.1f} |
""")

if __name__ == "__main__":
    asyncio.run(main())