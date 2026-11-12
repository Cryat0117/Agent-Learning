"""
async_core.tests.test_ratelimit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
针对 AsyncTokenBucket 的全覆盖自动化单元测试集 (TDD 规范)
"""

import asyncio
import time
import pytest
from async_core.ratelimit import AsyncTokenBucket


@pytest.mark.asyncio
async def test_invalid_init_parameters():
    """测试初始化非法参数拦截：rate 和 capacity 必须为正数。"""
    with pytest.raises(ValueError, match="rate 必须为正数"):
        AsyncTokenBucket(rate=0, capacity=10)

    with pytest.raises(ValueError, match="rate 必须为正数"):
        AsyncTokenBucket(rate=-5, capacity=10)

    with pytest.raises(ValueError, match="capacity 必须为正数"):
        AsyncTokenBucket(rate=10, capacity=0)

    with pytest.raises(ValueError, match="capacity 必须为正数"):
        AsyncTokenBucket(rate=10, capacity=-1)


@pytest.mark.asyncio
async def test_invalid_acquire_parameters():
    """测试申请非法令牌数拦截：tokens 必须 > 0 且 <= capacity。"""
    bucket = AsyncTokenBucket(rate=10, capacity=5)

    with pytest.raises(ValueError, match="必须为正数"):
        await bucket.acquire(0)

    with pytest.raises(ValueError, match="必须为正数"):
        await bucket.acquire(-2)

    with pytest.raises(ValueError, match="超出了桶的最大容量"):
        await bucket.acquire(6)  # 单次申请 6 超过了容量 5，立刻报错拦截死锁


@pytest.mark.asyncio
async def test_burst_within_capacity():
    """测试突发流量支持：初始桶满，瞬间消费容量内的所有令牌耗时接近 0。"""
    bucket = AsyncTokenBucket(rate=2, capacity=5)

    t_start = time.perf_counter()
    # 瞬间并发申请 5 个令牌 (刚好打满 capacity)
    results = await asyncio.gather(*(bucket.acquire(1.0) for _ in range(5)))
    duration = time.perf_counter() - t_start

    # 5 个请求全部没有经历限流等待 (waited == 0)
    for waited in results:
        assert waited == 0.0

    # 耗时应当极短 (通常 < 0.05 秒)
    assert duration < 0.05


@pytest.mark.asyncio
async def test_rate_limiting_wait():
    """测试令牌不足时的限流等待机理：准确补发，平滑放行。"""
    # 速率：10 个/秒（即每 0.1 秒生成 1 个），容量：2 个
    bucket = AsyncTokenBucket(rate=10, capacity=2)

    # 1. 先消耗完桶内的 2 个初始令牌 (burst)
    w1 = await bucket.acquire(1.0)
    w2 = await bucket.acquire(1.0)
    assert w1 == 0.0
    assert w2 == 0.0

    # 2. 此时桶已空，申请第 3 个令牌，必须等待约 0.1 秒
    t_start = time.perf_counter()
    waited = await bucket.acquire(1.0)
    elapsed = time.perf_counter() - t_start

    assert waited >= 0.08
    assert elapsed >= 0.08
    assert elapsed < 0.25  # 允许一定的系统调度开销容差


@pytest.mark.asyncio
async def test_concurrency_race_condition_safety():
    """测试高并发下的竞态条件安全：多个协程同时抢令牌，无负数超卖，耗时符合数学预期。"""
    # 容量 5，速率 20 个/秒 (每个令牌耗时 0.05s)
    bucket = AsyncTokenBucket(rate=20, capacity=5)

    # 15 个并发协程同时申请 1 个令牌
    # 前 5 个瞬间拿到，后 10 个需要补充: 10 / 20 = 0.50 秒
    t_start = time.perf_counter()
    await asyncio.gather(*(bucket.acquire(1.0) for _ in range(15)))
    total_time = time.perf_counter() - t_start

    # 总耗时应当在 0.45s ~ 0.75s 之间
    assert 0.45 <= total_time <= 0.75
    # 桶内剩余估算令牌应在合法范围 [0, capacity]
    assert 0.0 <= bucket.tokens <= bucket.capacity


@pytest.mark.asyncio
async def test_context_manager():
    """测试 async with 上下文管理器语法糖支持。"""
    bucket = AsyncTokenBucket(rate=5, capacity=2)

    async with bucket:
        pass  # 顺利消耗 1 个令牌

    assert bucket.tokens < 2.0


@pytest.mark.asyncio
async def test_cancellation_releases_lock():
    """测试超时或取消时的锁释放：协程在等待令牌时被 Cancelled，不得死锁后续请求。"""
    bucket = AsyncTokenBucket(rate=1, capacity=1)
    await bucket.acquire(1.0)  # 桶空

    # 启动一个需要等待 1 秒的后台任务，但在 0.05 秒后强制取消它
    async def cancelled_task():
        await bucket.acquire(1.0)

    task = asyncio.create_task(cancelled_task())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # 验证后续任务：当桶补充了令牌后，下一个正常任务必须能顺利获取锁，绝不发生永久死锁
    await asyncio.sleep(1.0)  # 等待令牌生成
    waited = await bucket.acquire(1.0)
    assert waited == 0.0