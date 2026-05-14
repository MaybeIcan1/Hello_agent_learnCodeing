import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import httpx

load_dotenv()

 #设置 Clash 的 HTTP 代理（你的是 7890）
proxy_url = "http://127.0.0.1:7890"

# 创建一个 httpx 客户端，强制使用代理，并关闭 SSL 验证（Clash 有时会引发证书问题）
http_client = httpx.Client(
    proxies=proxy_url,
    verify=False,          # 临时绕过 SSL 证书验证（仅在本地测试，不要在生产环境使用）
    timeout=60.0
)

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_BASE_URL"), 
)

def get_weather(city: str) -> str:
    """模拟查询天气，返回固定字符串"""
    # 实际可以调用真实天气 API，这里简单模拟
    return f"{city} 当前天气：晴朗，气温 22°C，适合户外活动。"

def get_attraction(city: str, weather: str = None) -> str:
    """根据城市和天气推荐景点"""
    if "雨" in weather or "rain" in weather.lower():
        return f"推荐 {city} 的室内景点：博物馆、美术馆。"
    else:
        return f"推荐 {city} 的户外景点：公园、山景、海滨。"
    
SYSTEM_PROMPT = """你是一个智能旅行助手，可以调用以下工具来回答用户问题：

工具列表：
1. get_weather(city: str) -> str   # 查询某城市的天气
2. get_attraction(city: str, weather: str = None) -> str  # 推荐景点

你的工作方式：
- 每次先输出你的思考（Thought）
- 然后输出你要调用的工具（Action），格式必须为 JSON：{"name": "工具名", "arguments": {"参数名": "参数值"}}
- 系统会执行工具并把结果以 Observation 返回给你
- 你可以多次重复思考-行动-观察，直到能够给出最终答案
- 最终答案用 Final Answer: 开头

示例：
Thought: 用户想了解北京的天气，我需要先查天气。
Action: {"name": "get_weather", "arguments": {"city": "北京"}}
--- 系统返回 Observation: 北京晴朗，22°C ---
Thought: 现在我知道天气晴朗，可以推荐室外景点。
Action: {"name": "get_attraction", "arguments": {"city": "北京", "weather": "晴朗"}}
--- 系统返回 Observation: 推荐故宫、颐和园 ---
Final Answer: 北京今天天气晴朗，推荐你去故宫和颐和园游玩。
"""

def execute_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "get_weather":
        return get_weather(**arguments)
    elif tool_name == "get_attraction":
        return get_attraction(**arguments)
    else:
        return f"错误：未知工具 {tool_name}"
    
def run_agent(user_question: str, max_steps: int = 5):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question}
    ]
    
    step = 0
    while step < max_steps:
        step += 1
        print(f"\n--- 步骤 {step} ---")
        
        # 调用 LLM
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",   # 或你有的其他模型
            messages=messages,
            temperature=0
        )
        assistant_msg = response.choices[0].message.content
        print("模型回复：")
        print(assistant_msg)
        
        # 将模型输出加入对话历史
        messages.append({"role": "assistant", "content": assistant_msg})
        
        # 检查是否包含 Final Answer
        if "Final Answer:" in assistant_msg:
            # 提取最终答案并返回
            final = assistant_msg.split("Final Answer:")[-1].strip()
            print("\n✅ 最终答案：", final)
            return final
        
        # 尝试解析 Action JSON
        # 寻找 "Action: {" 这样的模式
        import re
        json_match = re.search(r'Action:\s*(\{.*?\})', assistant_msg, re.DOTALL)
        if json_match:
            try:
                action_data = json.loads(json_match.group(1))
                tool_name = action_data["name"]
                arguments = action_data.get("arguments", {})
                print(f"🔧 执行工具：{tool_name}，参数：{arguments}")
                observation = execute_tool(tool_name, arguments)
                print(f"📋 观察结果：{observation}")
                # 将 Observation 加入对话
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            except Exception as e:
                print("解析 Action 出错：", e)
                messages.append({"role": "user", "content": f"Observation: 工具调用失败，错误：{e}"})
        else:
            # 没有 Action 也没有 Final Answer，要求模型继续
            messages.append({"role": "user", "content": "请继续，要么给出 Action 要么给出 Final Answer。"})
    
    print("达到最大步数，未得到最终答案。")
    return None

if __name__ == "__main__":
    question = input("请输入你的旅行问题：")
    run_agent(question)