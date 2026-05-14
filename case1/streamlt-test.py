import streamlit as st
import time
# 获得一个标题
st.title("前端-测试版")

# 分割线
st.divider()

# 消息输入框
prompt = st.chat_input("请输入你的问题：")

# 构建消息容器
if prompt:
    #一般设置两个对象，因为一个是询问者（一般是用户），和AI（助手）
    st.chat_message("user").markdown(prompt)

    #AI的回答
    with st.spinner("思考中"):
        time.sleep(1)
    st.chat_message("assistant").markdown("我不会")