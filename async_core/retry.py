"""
async_core.retry
~~~~~~~~~~~~~~~~
工业级异步重试装饰器 (Async Exponential Backoff with Full Jitter)

核心设计考量：
1. 指数退避与全抖动 (Full Jitter)：采用 AWS 架构经典算法，彻底粉碎并发重试风暴（Retry Storm）。
2. 白名单异常过滤 (Selective Retries)：仅对指定异常类型进行重试，非重试异常（如业务语法 Bug）立即快死（Fail-fast）。
3. 取消安全铁律 (Cancellation Safety)：Wall 2 经验落地，绝对不捕获、不重试 asyncio.CancelledError。
4. 防御性参数拦截 (Defensive Checks)：严格校验重试次数、基数延迟、最大封顶与倍数因子。
5. 装饰器元数据无损 (Metadata Preservation)：采用 functools.wraps 保持函数签名与 docstring。
"""

import asyncio
import functools
import random
from typing import Any, Callable, Coroutine, Tuple, Type


def async_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 10.0,
    factor: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """异步重试装饰器工厂函数。

    Args:
        max_retries (int): 最大重试次数 (默认 3 次)。
        base_delay (float): 初始重试延迟基数 (秒，默认 0.1s)。
        max_delay (float): 最大允许的重试封顶延迟 (秒，默认 10.0s)。
        factor (float): 指数退避底数 (默认 2.0，即每次翻倍)。
        jitter (bool): 是否开启 AWS Full Jitter 全随机抖动 (默认 True)。
        retry_on (Tuple[Type[Exception], ...]): 允许触发重试的异常类型元组。
    """
    # 🛡️ 边界防御：参数合法性校验
    if max_retries < 0:
        raise ValueError(f"max_retries 不能为负数，当前输入: {max_retries}")
    if base_delay <= 0:
        raise ValueError(f"base_delay 必须为正数，当前输入: {base_delay}")
    if max_delay < base_delay:
        raise ValueError(
            f"max_delay ({max_delay}) 不能小于 base_delay ({base_delay})！"
        )
    if factor < 1.0:
        raise ValueError(f"factor 不能小于 1.0，当前输入: {factor}")

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except asyncio.CancelledError:
                    # 🛡️ Wall 2 铁律：取消信号属于系统控制流，绝不能当成异常重试，必须直接向上冒泡！
                    raise
                except retry_on as exc:
                    attempt += 1
                    # 超过最大重试次数，耗尽重试机会，原汁原味抛出最后一次异常
                    if attempt > max_retries:
                        raise

                    # 1. 计算理论指数退避延迟上限：base * (factor ** (attempt - 1))
                    backoff = min(max_delay, base_delay * (factor ** (attempt - 1)))

                    # 2. AWS Full Jitter：在 [0, backoff] 间完全均匀随机取值，将重试波峰彻底抹平
                    if jitter:
                        sleep_time = random.uniform(0.0, backoff)
                    else:
                        sleep_time = backoff

                    # 3. 协作式挂起，交出事件循环控制权
                    await asyncio.sleep(sleep_time)

        return wrapper

    return decorator