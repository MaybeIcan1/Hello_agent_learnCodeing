import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any  



#加载.env文件中的环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class HelloAgentLLM:
    """
    为HelloAgent定制的LL客户端
    调用任何兼容OpenAI API的LLM服务都可以使用这个类进行封装，并默认流式响应
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("OPENAI_API_KEY")
        baseUrl = baseUrl or os.getenv("OPENAI_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回响应
        """
        print(f"LLM正在思考，模型：{self.model}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

            #处理流式响应
            print("LLM响应成功：")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)  #实时输出内容
                collected_content.append(content)
            print("\nLLM响应结束。")
            return "".join(collected_content)
        
        except Exception as e:
            print(f"调用LLM时发生错误: {e}")
            return None

#客户端使用示例
if __name__ == "__main__":
    try:
        llm_client = HelloAgentLLM()
        messages = [
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "请介绍一下HelloAgent是什么？"}
        ]
        print("正在调用LLM进行思考...")
        response = llm_client.think(messages)
        if response:
            print(f"LLM最终响应：{response}")

    except ValueError as e:
        print(f"运行时发生错误: {e}")