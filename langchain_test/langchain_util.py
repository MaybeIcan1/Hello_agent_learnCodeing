from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.tongyi import Tongyi
import os

# 创建内存对象
memory = ConversationBufferMemory(return_message = True)
api_key_zr = "sk-f0cee2ec30d94516a91c9a75b9f41960"

def get_response(prompt,api_key):
    model = Tongyi(model = "qwen-max",api_key =api_key_zr)
    chain = ConversationChain(llm=model, memory=memory)

    #发送用户请求
    response = chain.invoke({"input": prompt}) #返回字典
    return response['response']

if __name__ == "__main__":
    print(get_response("请用python输出1-10",api_key_zr))