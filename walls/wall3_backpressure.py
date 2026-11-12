# D:\Agent-Learning\walls\wall3_backpressure.py
import asyncio
import os
import time
import psutil

# 获取当前 Python 进程对象，用于精确监测真实物理内存占用 (MB)
proc = psutil.Process(os.getpid())

def get_memory_mb() -> float:
    """获取当前进程占用的物理内存 (MB)"""
    return proc.memory_info().rss / (1024 * 1024)

# 模拟处理单个任务的协程（每个任务有一点点微小耗时）
async def mock_handler(item: int):
    await asyncio.sleep(0.0001)
    return item * 2

# ====================================================================
# ❌ 错版：gather + Semaphore（只限并发，不限内存 —— 典型的“无背压”隐患）
#
# 很多人以为加了 Semaphore(50) 就万事大吉了：
# “你看，我同一时刻只允许 50 个任务并发，这不是很安全吗？”
#
# 思考题（这就是这道墙的死穴）：
# 既然同一时刻最多只有 50 个在跑，那剩下的 29,950 个任务此刻在哪里？占不占内存？
# ====================================================================
# async def run_bad_no_backpressure(total_items: int = 30_000, concurrency: int = 50):
#     sem = asyncio.Semaphore(concurrency)
    
#     async def worker(item: int):
#         async with sem:
#             return await mock_handler(item)

#     print(f"--> [错版启动] 准备处理 {total_items} 个任务，并发限制: {concurrency}...")
#     mem_before = get_memory_mb()
#     t_start = time.perf_counter()

#     # ❌ 致命隐患就在这一行！
#     # 观察：这一行列表推导式在瞬间执行后，代码还没开始跑，内存发生了什么剧烈变化？
#     coros = [worker(i) for i in range(total_items)]
    
#     mem_after_create = get_memory_mb()
#     tasks_count = len(coros)
#     print(f"    [内存告警] 瞬间在内存堆积的协程对象数: {tasks_count} 个！")
#     print(f"    [内存告警] 初始内存: {mem_before:.1f} MB")
#     print(f"    [内存告警] 还没开始执行，内存已飙升至: {mem_after_create:.1f} MB (净暴增 +{mem_after_create - mem_before:.1f} MB)！")

#     print(f"--> [开始执行] 将这 {total_items} 个协程全部一次性塞进 asyncio.gather 调度队列...")
#     results = await asyncio.gather(*coros)
    
#     duration = time.perf_counter() - t_start
#     mem_final = get_memory_mb()
#     print(f"--> [错版结束] 全部完成！耗时: {duration:.2f} 秒 | 最终峰值内存: {mem_final:.1f} MB")
#     print(f"--> [复盘总结] 从头到尾总内存净增量: +{mem_final - mem_before:.1f} MB！")

# ====================================================================
# ✅ 对版：Queue(maxsize=N) + 生产者-消费者模式（真背压）
# 内存上限被死死锁在 queue_size + concurrency，坚如磐石！
# ====================================================================
async def run_good_with_backpressure(total_items: int = 30_000, concurrency: int = 50, queue_size: int = 100):
    # ✅ 核心防线：设置了 maxsize 的有限队列，满员即刻阻塞生产者！
    q = asyncio.Queue(maxsize=queue_size)
    results = []
    SENTINEL = object()  # 毒丸标志（通知消费者收工退出）
    print(f"--> [对版启动] 准备处理 {total_items} 个任务 (背压队列上限: {queue_size}, 并发工人: {concurrency})...")
    mem_before = get_memory_mb()
    t_start = time.perf_counter()
    peak_tasks = 0
    # 1. 生产者：只负责供货。但只要队列装满了 100 个，await q.put(i) 就会立刻挂起等待！
    async def producer():
        for i in range(total_items):
            await q.put(i)  # 👈 核心背压点：队列达 100 时强行暂停，绝不多吃 1 字节内存！
        # 生产完毕后，向队列放入 concurrency 个结束标志（毒丸）
        for _ in range(concurrency):
            await q.put(SENTINEL)
    # 2. 消费者（固定数量的并发工人）：从队列取任务、执行、收工
    async def consumer():
        nonlocal peak_tasks
        while True:
            # 记录此时内存中真实存在的活跃任务总数
            peak_tasks = max(peak_tasks, len(asyncio.all_tasks()))
            item = await q.get()
            if item is SENTINEL:
                q.task_done()
                break
            res = await mock_handler(item)
            results.append(res)
            q.task_done()
    # 3. 启动 1 个生产者 + concurrency 个固定工人（全局一共只有 51 个协程常驻内存！）
    await asyncio.gather(producer(), *(consumer() for _ in range(concurrency)))
    duration = time.perf_counter() - t_start
    mem_final = get_memory_mb()
    print(f"    [内存监控] 任意时刻活跃协程数峰值: 仅 {peak_tasks} 个！（对比错版的 30,000 个）")
    print(f"    [内存监控] 初始内存: {mem_before:.1f} MB | 最终内存: {mem_final:.1f} MB (净波动仅 +{mem_final - mem_before:.1f} MB！)")
    print(f"--> [对版结束] 全部完成！耗时: {duration:.2f} 秒 | 产出结果数: {len(results)}")
    print(f"--> [对版复盘] 总内存净增量: 仅 +{mem_final - mem_before:.1f} MB！")

async def main():
    print("=" * 65)
    print(" 🧱 墙 3 终极对决：【无背压 (内存爆炸)】vs【有背压 (内存如磐石)】")
    print("=" * 65 + "\n")
    print("【第一回合：运行无背压错版】")
    await run_bad_no_backpressure(total_items=30_000, concurrency=50)
    
    print("\n" + "-" * 65 + "\n")
    print("【第二回合：运行有背压对版】")
    await run_good_with_backpressure(total_items=30_000, concurrency=50, queue_size=100)

if __name__ == "__main__":
    asyncio.run(main())