import os
import json
import time
from functools import wraps
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # 从 .env 文件加载环境变量
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY 环境变量。")

MODEL_NAME = "qwen-plus"  # 选择模型名称
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

class AddParams(BaseModel):
    """计算两个整数相加"""
    a: int = Field(description="第一个整数")
    b: int = Field(description="第二个整数")

class MultiplyParams(BaseModel):
    """计算两个整数相乘"""
    a: int = Field(description="第一个整数")
    b: int = Field(description="第二个整数")

def build_tool_schema(param_model: type[BaseModel], name: str, description: str) -> dict:
    """
    从 Pydantic 模型自动导出 Function Calling Schema（0 处手写字典，1 处自动生成）
    1. 通过 Pydantic 的 schema() 方法获取参数模型的 JSON Schema
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description or (param_model.__doc__ or "无描述"),
            "parameters": param_model.model_json_schema()  # 自动生成参数 JSON Schema
        }
    }

def timed(func):
    """工程级装饰器：自动统计工具耗时 (毫秒)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        print(f"[计时] 函数 {func.__name__} 执行时间: {duration_ms} 毫秒")
        return result, duration_ms
    return wrapper

@timed
def add(a: int, b: int) -> str:
    """计算两个整数的和"""
    return str(a + b)

@timed
def multiply(a: int, b: int) -> str:
    """计算两个整数的积"""
    return str(a * b)

tool_registry = {
    "add": {"func": add, "model": AddParams, "desc": "计算两个整数的和"},
    "multiply": {"func": multiply, "model": MultiplyParams, "desc": "计算两个整数相乘"}
}

tools = [
    build_tool_schema(info["model"], name=name, description=info["desc"])
    for name, info in tool_registry.items()
]

def run_agent(query: str, max_steps: int = 5):
    """
    运行一个简单的 Agent，使用 Function Calling 与工具交互
    1. query: 用户输入的自然语言问题
    2. max_steps: 最大交互轮数，防止无限循环
    """
    messages = [
        {"role": "system", "content": "你是一个严谨的计算助手。必须严格使用提供的工具进行计算，不要自行心算。"},
        {"role": "user", "content": query}
    ]

    print(f"\n[用户提问]: {query}\n" + "-" * 50)

    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools
        )
        message = resp.choices[0].message
        messages.append(message)  # 将模型回复加入对话历史

        if not message.tool_calls:
            print(f"\n[最终回答] (共思考 {step + 1} 轮):\n{message.content}")
            return message.content

        for call in message.tool_calls:
            fn_name = call.function.name
            print(f"-> 步骤 {step + 1}: 模型决策调用 `{fn_name}` | 原始参数: {call.function.arguments}")

            tool_entry = tool_registry.get(fn_name)
            if not tool_entry:
                res_content = f"Error: 未知工具 {fn_name}"
            else:
                try:
                    # 1. 原始 JSON 反序列化
                    raw_args = json.loads(call.function.arguments)
                    # 2. 核心拦截：用 Pydantic 模型实例化进行运行时类型校验
                    param_obj = tool_entry["model"](**raw_args)
                    # 3. 校验通过，解包执行真实工具（接收计算结果与耗时）
                    calc_res, duration_ms = tool_entry["func"](**param_obj.model_dump())
                    res_content = calc_res
                    print(f"<- 步骤 {step + 1}: 工具 `{fn_name}` 执行成功 (耗时: {duration_ms}ms) | 结果: {res_content}")
                except ValidationError as val_err:
                    res_content = f"Error: 参数校验失败: {val_err.errors()}"
                    print(f"⚠️ 步骤 {step + 1}: 参数契约校验拦截: {res_content}")
                except Exception as e:
                    res_content = f"Error: 工具执行失败: {e}"
                    print(f"❌ 步骤 {step + 1}: 工具异常: {res_content}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": res_content})
    print(f"⚠️ 达到最大思考轮数 ({max_steps})，强制停止。")
    return None

if __name__ == "__main__":
    print("🤖 智能计算 Agent 已就绪！(输入 'exit' 或 'q' 退出)")
    while True:
        try:
            user_input = input("\n请输入计算问题: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("👋 感谢使用，Agent 已安全退出。")
                break
            run_agent(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 接收到退出信号，Agent 安全退出。")
            break