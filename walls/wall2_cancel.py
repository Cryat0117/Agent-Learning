# D:\Agent-Learning\walls\wall2_cancel.py
import asyncio
import time

# 信号量设置为 1：同时只允许 1 个任务执行
sem = asyncio.Semaphore(1)

# async def bad_worker(i: int):
#     await sem.acquire()
#     print(f"[{time.strftime('%X')}] 任务 {i} 拿到信号量，开始执行耗时操作...")
#     # try:
#     #     await asyncio.sleep(10)  # 模拟耗时 10 秒的长请求
#     #     sem.release()
#     # except BaseException:        # ❌ 致命错误：裸捕获/捕获了 BaseException，把 CancelledError 也吞了！
#     #     print(f"[{time.strftime('%X')}] 任务 {i} 异常退出，直接 return！")
#     #     return                   # ❌ 此时 release() 永远不会被调用！信号量永久丢失！

#     # ✅ 修复方案 1：手动配对 finally（确保超时/取消时 100% 释放信号量）
#     try:
#         await asyncio.sleep(0.5)
#     finally:
#         sem.release()
#         print(f"[{time.strftime('%X')}] 任务 {i} 在 finally 中安全释放了信号量！")

# ✅ 修复方案 2（工业界最佳实践）：使用异步上下文管理器 async with
async def good_worker(i: int):
    async with sem:
        print(f"[{time.strftime('%X')}] 任务 {i} [async with] 获得门票，执行中...")
        await asyncio.sleep(0.5)
        print(f"[{time.strftime('%X')}] 任务 {i} [async with] 自动归还门票，安全收工！")

async def run_test():
    print("=== 开始运行【修复版测试】：验证超时取消不再死锁 ===\n")
    
    # 1. 任务 0 执行 0.1 秒后被客户端主动超时取消 (wait_for)
    try:
        print(f"[{time.strftime('%X')}] 主流程：发起任务 0 (限时 0.1 秒)...")
        await asyncio.wait_for(good_worker(0), timeout=0.1)
    except asyncio.TimeoutError:
        print(f"[{time.strftime('%X')}] 主流程：任务 0 超时被取消！\n")

    # 2. 验证任务 1 能否立刻接手门票（不再卡死）
    print(f"[{time.strftime('%X')}] 主流程：发起任务 1 (验证信号量已被安全还回)...")
    await good_worker(1)
    print(f"[{time.strftime('%X')}] 主流程：任务 1 顺利完成，死锁解除！\n")

    # 3. 验证 async with 终极优雅形态
    print(f"[{time.strftime('%X')}] 主流程：测试现代推荐做法 (good_worker)...")
    await good_worker(2)
    print("\n🎉 全部测试顺利通过！")

if __name__ == "__main__":
    asyncio.run(run_test())
