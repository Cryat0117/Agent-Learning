# D:\Agent-Learning\demo_wall1_blocking.py
import asyncio
import time

async def handle(i: int):
    print(f"[{time.strftime('%X')}] 协程 {i} 开始执行...")
    await asyncio.sleep(0.5)  # time.sleep(0.5)  # ❌ 致命陷阱：在协程内部调用了同步阻塞函数
    print(f"[{time.strftime('%X')}] 协程 {i} 执行完毕！")
    return i

async def main():
    t_start = time.perf_counter()
    # 模拟并发发起 3 个请求
    results = await asyncio.gather(*(handle(i) for i in range(3)))
    duration = time.perf_counter() - t_start
    print("-" * 40)
    print(f"全部完成！返回值: {results}")
    print(f"总耗时: {duration:.2f} 秒")

if __name__ == "__main__":
    asyncio.run(main())