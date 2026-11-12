"""
AsyncTokenBucket: 异步令牌桶限流器 (支持突发与并发安全)
将在 W6 第一组件任务中实现。
"""
"""
async_core.ratelimit
~~~~~~~~~~~~~~~~~~~~
工业级异步令牌桶限流器 (Async Token Bucket Rate Limiter)

核心设计考量：
1. 惰性求值 (Lazy Evaluation)：基于 time.monotonic() 计算时间差补发令牌，零后台定时任务，零轮询开销。
2. 突发容忍 (Burst Support)：初始令牌为 capacity，允许瞬间爆发消费最多 capacity 个令牌。
3. 精确等待 (Precise Backoff)：当令牌不足时，计算精确缺失令牌所需的恢复等待时间，通过 await asyncio.sleep() 协作式挂起。
4. 并发互斥 (Async Concurrency Safe)：使用 asyncio.Lock() 保护令牌计算与扣减，防止并发竞态条件（Race Condition）导致超卖。
5. 严格防御性校验 (Defensive Programming)：拦截非法 rate、capacity 及单次请求大于容量的死锁陷阱。
6. 上下文管理器语法糖 (Context Manager)：支持 `async with bucket:` 优雅调用。
"""

import asyncio
import time
from typing import Optional


class AsyncTokenBucket:
    """异步令牌桶限流器。

    Attributes:
        rate (float): 令牌填充速率 (每秒生成令牌数，必须 > 0)。
        capacity (float): 令牌桶容量 (允许的最大突发累积量，必须 > 0)。
    """

    def __init__(self, rate: float, capacity: float):
        # 🛡️ 边界防御：速率与容量必须为合法正数
        if rate <= 0:
            raise ValueError(f"rate 必须为正数，当前输入: {rate}")
        if capacity <= 0:
            raise ValueError(f"capacity 必须为正数，当前输入: {capacity}")

        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)  # 初始桶满，支持初始瞬时突发 (Burst)
        self._last_updated = time.monotonic()  # 单调递增时钟，不受系统改时间影响
        self._lock = asyncio.Lock()  # 异步互斥锁，保证并发扣减安全

    @property
    def tokens(self) -> float:
        """只读属性：获取当前估算的可用令牌数（仅用于监控与可观测性打点）。"""
        now = time.monotonic()
        delta = max(0.0, now - self._last_updated)
        return min(self.capacity, self._tokens + delta * self.rate)

    def _refill(self, now: float) -> None:
        """内部方法：在持有锁的情况下，基于时间差惰性补水。"""
        delta = max(0.0, now - self._last_updated)
        self._tokens = min(self.capacity, self._tokens + delta * self.rate)
        self._last_updated = now

    async def acquire(self, tokens: float = 1.0) -> float:
        """异步申请获取指定数量的令牌。

        Args:
            tokens (float): 需要消耗的令牌数，默认为 1.0。

        Returns:
            float: 本次请求实际累计等待的时间（秒）。若未发生等待，返回 0.0。

        Raises:
            ValueError: 当 tokens <= 0 或 tokens > capacity 时抛出。
        """
        # 🛡️ 参数合法性防御
        if tokens <= 0:
            raise ValueError(f"申请的令牌数 tokens 必须为正数，当前输入: {tokens}")
        # 🛡️ 致命死锁拦截：单次申请大于桶容量时，由于桶容量是上限，此请求永远无法满足，必须立即报错！
        if tokens > self.capacity:
            raise ValueError(
                f"申请的令牌数 ({tokens}) 超出了桶的最大容量 ({self.capacity})，该请求永远无法满足！"
            )

        total_waited = 0.0

        async with self._lock:
            while True:
                now = time.monotonic()
                self._refill(now)

                # 情况 A：桶内令牌充足，直接扣减并返回总等待耗时
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return total_waited

                # 情况 B：令牌不足，精准计算缺口和需要睡眠的时长
                deficit = tokens - self._tokens
                wait_time = deficit / self.rate

                # 协作式挂起，交出事件循环控制权
                # 持锁等待确保 FIFO 严格排队，防止后到任务插队抢跑
                await asyncio.sleep(wait_time)
                total_waited += wait_time

    async def __aenter__(self):
        """支持 async with bucket: 语法糖 (默认消耗 1 个令牌)。"""
        await self.acquire(1.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文退出（无需释放令牌，令牌已被消费）。"""
        pass