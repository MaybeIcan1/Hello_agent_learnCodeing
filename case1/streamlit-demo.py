import streamlit as st      
import time

# 初始化消息列表
if "messages" not in st.session_state:
    st.session_state["messages"] = []  
    
# title
st.title("demo")

# 标题分割线
st.divider()

# 消息输入框
prompt = st.chat_input("请输入你的问题：")

# # 消息容器
# if prompt:
#     st.chat_message("user").markdown(prompt) # 用户消息展示

#     response = "我在烧烤"   # 模拟回复
#     with st.spinner("AI正在思考..."):
#         time.sleep(2)  
#     st.chat_message("assistant").markdown(response)

#每一次调用streamlit就是运行一次本文件，所以会保存不了会话，要引入新的api

#1.角色 一次对话={“role”:“user/assistant”,“content”:“内容”}，天然像字典的形式
#2.消息列表：要存历史会话就要有很多个一次会话，所以用列表


if prompt:
    st.session_state['messages'].append({"role":"user","content":prompt}) # 用户消息添加到列表
    for message in st.session_state['messages']:
        st.chat_message(message["role"]).markdown(message["content"]) # 展示历史消息
        
    with st.spinner("AI正在思考..."):
        time.sleep(2)
        response = "我在烧烤"   # 模拟回复
        st.session_state['messages'].append({"role":"assistant","content":response}) # 回复消息添加到列表
        st.chat_message("assistant").markdown(response)  # 展示回复消息