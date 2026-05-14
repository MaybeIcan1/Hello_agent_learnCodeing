from langchain_util import get_response
from langchain_util import api_key_zr
import streamlit as st

#初始化消息记录
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# 添加标题 
st.title("Streamlit Chat with LangChain and Tongyi Qwen")

# 添加分割线
st.divider()

# 消息输入框
prompt = st.chat_input("请输入你的问题：")

if prompt:
    # 用户消息添加到列表
    st.session_state['messages'].append({"role":"user","content":prompt})
    # 输出历史信息在消息容器中
    for message in st.session_state['messages']:
        st.chat_message(message["role"]).markdown(message["content"])

    with st.spinner("AI正在思考..."):
        response = get_response(prompt,api_key="api_key_zr")
        #从response中取出messages中的content
        st.session_state['messages'].append({"role":"assistant","content":response})
        # 在消息容器中渲染回答
        st.chat_message("assistant").markdown(response)