"""
async_core.tests.test_worker_pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
针对 bounded_worker_pool 的全覆盖自动化单元测试集 (TDD 规范)
"""

import asyncio
import pytest
from async_core.worker_pool import bounded_worker_pool


@pytest.mark.asyncio
async def test_invalid_parameters():
    """测试非法参数拦截：concurrency 和 queue_size 必须为正数。"""
    async def dummy(x):
        return x

    with pytest.raises(ValueError, match="concurrency 必须为正数"):
        await bounded_worker_pool([1], dummy, concurrency=0)

    with pytest.raises(ValueError, match="queue_size 必须为正数"):
        await bounded_worker_pool([1], dummy, queue_size=-1)


@pytest.mark.asyncio
async def test_empty_items():
    """测试空任务集：零任务秒级返回空列表。"""
    async def dummy(x):
        return x

    results = await bounded_worker_pool([], dummy, concurrency=5)
    assert results == []


@pytest.mark.asyncio
async def test_normal_execution_and_results():
    """测试常规处理：所有输入项均被正确处理且数量一致。"""
    async def double(x):
        await asyncio.sleep(0.001)
        return x * 2

    inputs = list(range(100))
    results = await bounded_worker_pool(inputs, double, concurrency=10, queue_size=20)

    assert len(results) == 100
    assert sorted(results) == [x * 2 for x in inputs]


@pytest.mark.asyncio
async def test_concurrency_and_backpressure_bound():
    """测试背压与活跃协程数边界：无论输入多大，活跃协程数绝不失控。"""
    active_workers = 0
    max_active_observed = 0

    async def tracking_handler(x):
        nonlocal active_workers, max_active_observed
        active_workers += 1
        max_active_observed = max(max_active_observed, active_workers)
        await asyncio.sleep(0.005)
        active_workers -= 1
        return x

    # 塞入 500 个任务，限制并发 10 个
    total_tasks = 500
    concurrency_limit = 10
    results = await bounded_worker_pool(
        items=range(total_tasks),
        handler=tracking_handler,
        concurrency=concurrency_limit,
        queue_size=20,
    )

    assert len(results) == total_tasks
    # 任何时刻正在干活的工人数绝不能超过 concurrency 限制！
    assert max_active_observed <= concurrency_limit


@pytest.mark.asyncio
async def test_exception_fail_fast():
    """测试异常熔断：遇到未捕获异常立刻退出并传播异常。"""
    async def flawed_handler(x):
        if x == 10:
            raise RuntimeError("第 10 号任务致命崩溃！")
        await asyncio.sleep(0.001)
        return x

    with pytest.raises(RuntimeError, match="第 10 号任务致命崩溃"):
        await bounded_worker_pool(range(50), flawed_handler, concurrency=5, return_exceptions=False)


@pytest.mark.asyncio
async def test_return_exceptions_mode():
    """测试容错模式：return_exceptions=True 时将异常作为结果收集，不打断整体流程。"""
    async def tolerant_handler(x):
        if x % 2 == 0:
            raise ValueError(f"偶数 {x} 报错")
        return x * 10

    results = await bounded_worker_pool(range(10), tolerant_handler, concurrency=3, return_exceptions=True)

    assert len(results) == 10
    # 检查其中有 5 个是异常，5 个是正常结果
    exceptions = [r for r in results if isinstance(r, Exception)]
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(exceptions) == 5
    assert len(successes) == 5


@pytest.mark.asyncio
async def test_external_cancellation():
    """测试外层取消安全：外部取消 pool 时，子任务被妥善 cancel，绝不悬挂后台。"""
    started = 0

    async def hanging_handler(x):
        nonlocal started
        started += 1
        await asyncio.sleep(10.0)  # 长期挂起

    pool_task = asyncio.create_task(
        bounded_worker_pool(range(20), hanging_handler, concurrency=5, queue_size=5)
    )

    await asyncio.sleep(0.05)
    # 此时应该有 5 个工人已启动
    assert started == 5

    # 外部强行取消
    pool_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pool_task