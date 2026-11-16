"""
mock_server.py
~~~~~~~~~~~~~~
W6 专用本地测试服务器 (FastAPI)
模拟远程大模型/HTTP 服务的延迟与瞬态故障。
"""

import asyncio
import random
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/delay")
async def delay_endpoint():
    # 模拟真实远程 API 延迟 U(100, 500) ms
    cost = random.uniform(0.10, 0.50)
    await asyncio.sleep(cost)

    # 注入 2% 的微量偶发 502 网络故障，检验 @async_retry 自愈能力
    if random.random() < 0.02:
        raise HTTPException(status_code=502, detail="Mock Bad Gateway")

    return {"status": "ok", "cost_s": cost}