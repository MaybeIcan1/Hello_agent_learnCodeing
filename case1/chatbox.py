import ollama
import streamlit as st

#获取客户端
client = ollama.Client(host="http://localhost:11434")

#初始化消息记录
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# 添加标题 
st.title("Streamlit Chat with Ollama")

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
        response = client.chat(
            model = "deepseek-r1:8b",
            messages = st.session_state['messages'] #注意 这样的回答是无法考虑上下文的，ai只会记住这一次对话，只是用容器展示了历史对话
        )
        #从response中取出messages中的content
        st.session_state['messages'].append({"role":"assistant","content":response['message']['content']})
        # 在消息容器中渲染回答
        st.chat_message("assistant").markdown(response['message']['content'])