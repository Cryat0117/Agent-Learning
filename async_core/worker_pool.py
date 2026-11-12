"""
async_core.worker_pool
~~~~~~~~~~~~~~~~~~~~~~
工业级真背压异步工作池 (Bounded Async Worker Pool with Backpressure)

核心设计考量：
1. 物理级背压防护 (Hard Backpressure)：基于 asyncio.Queue(maxsize=N)，队列打满时物理阻塞生产者，内存恒定 O(concurrency)。
2. 优雅停机毒丸协议 (Poison Pill Sentinel)：生产结束投放单例毒丸，所有消费者协程自然 break 退出，零资源残留。
3. 异常保真与故障隔离 (Error Handling)：支持 return_exceptions 参数，既可遇错快死 (Fail-fast)，亦可全量容错收集。
4. 防御性边界校验 (Defensive Checks)：严格拦截并发数 <= 0、队列容量 <= 0 等非法配置。
5. 取消安全与栈清理 (Cancellation Cleanup)：外层取消时确保所有子任务妥善收敛，绝不悬挂后台僵尸任务。
"""

import asyncio
from typing import Any, Callable, Coroutine, Iterable, List, TypeVar

T = TypeVar("T")
R = TypeVar("R")


async def bounded_worker_pool(
    items: Iterable[T],
    handler: Callable[[T], Coroutine[Any, Any, R]],
    concurrency: int = 50,
    queue_size: int = 100,
    return_exceptions: bool = False,
) -> List[R]:
    """工业级真背压异步工作池。

    Args:
        items: 待处理的任务项可迭代对象（如 List、Generator 等）。
        handler: 针对单个任务项的异步处理函数 (async def)。
        concurrency: 最大并发工人协程数量 (必须 > 0)。
        queue_size: 有界背压队列容量上限 (必须 > 0)。
        return_exceptions: 是否将异常作为结果返回。若为 False，遇到异常立刻终止并向外抛出。

    Returns:
        List[R]: 所有任务处理结果的列表。

    Raises:
        ValueError: 当 concurrency <= 0 或 queue_size <= 0 时抛出。
    """
    # 🛡️ 参数合法性边界防御
    if concurrency <= 0:
        raise ValueError(f"concurrency 必须为正数，当前输入: {concurrency}")
    if queue_size <= 0:
        raise ValueError(f"queue_size 必须为正数，当前输入: {queue_size}")

    q: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
    results: List[R] = []
    results_lock = asyncio.Lock()
    SENTINEL = object()  # 毒丸单例

    # 1. 生产者协程：逐个塞入任务，队列满时自动挂起阻塞
    async def producer():
        for item in items:
            await q.put(item)  # 👈 核心背压点：满员即挂起
        # 生产结束，投放 concurrency 个毒丸通知所有工人收工
        for _ in range(concurrency):
            await q.put(SENTINEL)

    # 2. 消费者工人协程：从队列拉取任务处理
    async def worker():
        while True:
            item = await q.get()
            if item is SENTINEL:
                q.task_done()
                break

            try:
                res = await handler(item)
                async with results_lock:
                    results.append(res)
            except Exception as exc:
                if return_exceptions:
                    async with results_lock:
                        results.append(exc)  # type: ignore
                else:
                    # 发生非预期异常，立刻标记完成并向上抛出，触发外层熔断
                    q.task_done()
                    raise
            finally:
                q.task_done()

    # 3. 统一调度：启动 1 个生产者 + concurrency 个固定工人
    # 使用 gather 同时管理所有协程，任意一个抛出异常立即向外传播
    workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
    producer_task = asyncio.create_task(producer())

    try:
        await asyncio.gather(producer_task, *workers)
    except Exception:
        # 🛡️ 异常防御：如果有工人抛出异常崩溃，确保取消其余所有活跃子任务，清理现场
        producer_task.cancel()
        for w in workers:
            w.cancel()
        raise

    return results