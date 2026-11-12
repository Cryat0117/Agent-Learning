"""
async_core.tests.test_retry
~~~~~~~~~~~~~~~~~~~~~~~~~~~
针对 async_retry 装饰器的全覆盖自动化单元测试集 (TDD 规范)
"""

import asyncio
import time
import pytest
from async_core.retry import async_retry


@pytest.mark.asyncio
async def test_invalid_parameters():
    """测试装饰器初始化非法参数拦截。"""
    with pytest.raises(ValueError, match="max_retries 不能为负数"):
        async_retry(max_retries=-1)

    with pytest.raises(ValueError, match="base_delay 必须为正数"):
        async_retry(base_delay=0)

    with pytest.raises(ValueError, match="max_delay .* 不能小于 base_delay"):
        async_retry(base_delay=5.0, max_delay=2.0)

    with pytest.raises(ValueError, match="factor 不能小于 1.0"):
        async_retry(factor=0.5)


@pytest.mark.asyncio
async def test_success_on_first_try():
    """测试一次成功：不触发重试，零等待，原样返回结果。"""
    calls = 0

    @async_retry(max_retries=3)
    async def ok_task():
        nonlocal calls
        calls += 1
        return "success"

    result = await ok_task()
    assert result == "success"
    assert calls == 1


@pytest.mark.asyncio
async def test_success_after_retries():
    """测试前两次失败、第三次成功：调用 3 次，最终返回正常结果。"""
    calls = 0

    @async_retry(max_retries=3, base_delay=0.01, jitter=False)
    async def flaky_task():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("网络瞬时抖动")
        return "recovered"

    result = await flaky_task()
    assert result == "recovered"
    assert calls == 3


@pytest.mark.asyncio
async def test_exhaust_retries_raises_last_exception():
    """测试重试耗尽：超过 max_retries 后，如实抛出最后一次的异常。"""
    calls = 0

    @async_retry(max_retries=2, base_delay=0.01, jitter=False)
    async def always_fails():
        nonlocal calls
        calls += 1
        raise TimeoutError(f"第 {calls} 次超时")

    with pytest.raises(TimeoutError, match="第 3 次超时"):
        await always_fails()

    # 初始 1 次 + 重试 2 次 = 共执行 3 次
    assert calls == 3


@pytest.mark.asyncio
async def test_non_retryable_exception_fails_fast():
    """测试非白名单异常：不属于 retry_on 的异常立即向外抛出，绝不浪费时间重试。"""
    calls = 0

    @async_retry(max_retries=5, retry_on=(ConnectionError,))
    async def logic_error_task():
        nonlocal calls
        calls += 1
        raise ValueError("业务参数错误，重试无用")

    with pytest.raises(ValueError, match="业务参数错误"):
        await logic_error_task()

    # 只调用了 1 次，立刻快死（Fail-fast）
    assert calls == 1


@pytest.mark.asyncio
async def test_cancellation_is_never_retried():
    """测试取消安全（Wall 2 铁律）：任务被 cancel 时必须立即中断，绝不能捕获并重试。"""
    calls = 0

    @async_retry(max_retries=5, base_delay=0.5)
    async def slow_task():
        nonlocal calls
        calls += 1
        await asyncio.sleep(1.0)

    task = asyncio.create_task(slow_task())
    await asyncio.sleep(0.05)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    # 只能执行 1 次，取消后立即退出，绝没有发生第 2 次重试
    assert calls == 1


@pytest.mark.asyncio
async def test_exponential_backoff_timing():
    """测试指数退避时间计算：不加抖动时，重试延迟严格按指数倍增。"""
    # 基础延迟 0.05s，倍数 2.0，重试 2 次
    # 第 1 次重试延迟: 0.05 * (2^0) = 0.05s
    # 第 2 次重试延迟: 0.05 * (2^1) = 0.10s
    # 理论累计等待时间: 0.05 + 0.10 = 0.15s
    @async_retry(max_retries=2, base_delay=0.05, factor=2.0, jitter=False)
    async def timed_task():
        raise RuntimeError("boom")

    t_start = time.perf_counter()
    with pytest.raises(RuntimeError):
        await timed_task()
    duration = time.perf_counter() - t_start

    # 耗时应当在 0.14s ~ 0.30s 之间
    assert 0.14 <= duration <= 0.30