import os
import re
import requests
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# --- OpenAI兼容客户端类 ---
class OpenAICompatibleClient:
    """用于调用任何兼容OpenAI接口的LLM服务的客户端"""
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应"""
        # 清理无效的Unicode代理字符
        def clean_text(text):
            return text.encode('utf-8', errors='ignore').decode('utf-8')

        # 使用Clash代理访问DeepSeek
        proxy_url = "http://127.0.0.1:7890"
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=httpx.Client(proxy=proxy_url)
            )
            messages = [
                {'role': 'system', 'content': clean_text(system_prompt)},
                {'role': 'user', 'content': clean_text(prompt)}
            ]
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"


# --- 工具函数 ---
def get_weather(city: str) -> str:
    """通过调用 wttr.in API 查询真实的天气信息"""
    url = f"https://wttr.in/{city}?format=j1"
    # 国外API走代理，DeepSeek直连不走代理
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()
        data = response.json()
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """根据城市和天气推荐景点"""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误: 未找到Tavily API密钥，请检查环境变量设置。"

    # Tavily是国外服务，需要走代理
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
    tavily = TavilyClient(api_key=api_key)
    query = f"推荐{city}的旅游景点，当前天气是{weather}。请根据天气情况推荐适合的室内或室外景点。"

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"
        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"
    finally:
        # 清除代理环境变量，避免影响后续DeepSeek调用
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)


# 工具字典
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


# --- 系统提示词 ---
AGENT_SYSTEM_PROMPT = """你是一个智能旅行助手，可以调用以下工具来回答用户问题：

工具列表：
1. get_weather(city: str) -> str   # 查询某城市的天气
2. get_attraction(city: str, weather: str) -> str  # 推荐景点

你的工作方式：
- 每次先输出你的思考（Thought）
- 然后输出你要调用的工具（Action），格式为：Action: 工具名(参数名="参数值")
- 系统会执行工具并把结果以 Observation 返回给你
- 你可以多次重复思考-行动-观察，直到能够给出最终答案
- 最终答案用：Finish("你的答案")

示例：
Thought: 用户想了解北京的天气，我需要先查天气。
Action: get_weather(city="北京")
--- 系统返回 Observation: 北京晴朗，22°C ---
Thought: 现在我知道天气晴朗，可以推荐室外景点。
Action: get_attraction(city="北京", weather="晴朗")
--- 系统返回 Observation: 推荐故宫、颐和园 ---
Thought: 我已经获取了天气和景点信息，可以给出最终答案了。
Finish("北京今天天气晴朗，推荐你去故宫和颐和园游玩。")
"""


# --- 初始化LLM客户端 ---
llm = OpenAICompatibleClient(
    model=os.getenv("MODEL_ID", "deepseek-chat"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)


# --- 主函数 ---
def run_agent(user_question: str, max_steps: int = 5):
    prompt_history = [f"用户请求: {user_question}"]
    print(f"用户输入: {user_question}\n" + "="*40)

    for i in range(max_steps):
        print(f"\n--- 步骤 {i+1} ---\n")

        # 构建Prompt
        full_prompt = "\n".join(prompt_history)

        # 调用LLM
        llm_output = llm.generate(full_prompt, AGENT_SYSTEM_PROMPT)
        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 检查是否完成
        finish_match = re.search(r'Finish\("(.+?)"\)', llm_output, re.DOTALL)
        if finish_match:
            final_answer = finish_match.group(1)
            print(f"\n[最终答案] {final_answer}")
            return final_answer

        # 解析Action
        action_match = re.search(r"Action:\s*(\w+)\((.+?)\)", llm_output, re.DOTALL)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "="*40)
            prompt_history.append(observation_str)
            continue

        tool_name = action_match.group(1)
        args_str = action_match.group(2)

        # 解析参数
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        # 执行工具
        print(f"🔧 执行工具：{tool_name}，参数：{kwargs}")
        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误:未定义的工具 '{tool_name}'"

        observation_str = f"Observation: {observation}"
        print(f"📋 {observation_str}\n" + "="*40)
        prompt_history.append(observation_str)

    print("达到最大步数，未得到最终答案。")
    return None


if __name__ == "__main__":
    question = input("请输入你的旅行问题：")
    run_agent(question)
