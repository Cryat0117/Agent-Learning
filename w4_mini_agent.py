import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # 从 .env 文件加载环境变量
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("请在 .env 文件中设置 DASHSCOPE_API_KEY 环境变量。")

MODEL_NAME = "qwen3.8-flash" # 选择模型名称
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

def add(a: int, b:int) -> str:
    return str(a + b)
# def add(a: int, b: int) -> str:
#       raise ValueError("加法计算器模块硬件故障，连接超时！")
#   破坏性实验

def multiply(a: int, b:int) -> str:
    return str(a * b)

available_tools = { "add": add, "multiply": multiply }

tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "计算两个整数的和",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "第一个整数"},
                    "b": {"type": "integer", "description": "第二个整数"}
                },
                "required": ["a", "b"]
            }
        }
    },  
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "计算两个整数的积",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "第一个整数"},
                    "b": {"type": "integer", "description": "第二个整数"}
                },
                "required": ["a", "b"]
            }
        }
    }
]

def run_agent(query: str, max_steps: int = 5):
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
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print(f"[最终回答] (共思考 {step + 1} 轮):\n{msg.content}")
            return msg.content

        for call in msg.tool_calls:
            fn_name = call.function.name
            print(f"-> 步骤 {step + 1}: 模型决策调用 `{fn_name}` | 原始参数: {call.function.arguments}")

            tool_fn = available_tools.get(fn_name)
            if not tool_fn:
                res = f"Error: 未知工具 {fn_name}"
            else:
                try:
                    args = json.loads(call.function.arguments)
                    res = tool_fn(**args)
                except Exception as e:
                    res = f"Error: 工具执行失败: {e}"

            print(f"<- 步骤 {step + 1}: 工具返回: {res}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": res})

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
                print("👋 感谢使用,Agent 已安全退出。")
                break

            run_agent(user_input)

        except (KeyboardInterrupt, EOFError):
            print("\n👋 接收到退出信号,Agent 安全退出。")
            break