import streamlit as st
from rag import RagService
from redis_history_store import get_redis_history
from user_service import UserService

# 初始化用户服务
if "user_service" not in st.session_state:
    st.session_state["user_service"] = UserService()

# 页面配置
st.set_page_config(page_title="多用户智能客服", page_icon="🤖")

# --- 状态管理 ---
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False
# if "username" not in st.session_state:
#     st.session_state["username"] = ""
# 3. 【关键修改】状态管理 - 确保只在真正第一次加载时初始化
# 使用 setdefault 可以避免在刷新时被意外覆盖（虽然 if not in 也可以，但这样更稳健）
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", "")


# --- 侧边栏：登录/注册/退出 ---
with st.sidebar:
    st.title("用户中心")

    if not st.session_state["logged_in"]:
        tab1, tab2 = st.tabs(["登录", "注册"])

        with tab1:
            login_user = st.text_input("用户名", key="login_user")
            login_pwd = st.text_input("密码", type="password", key="login_pwd")
            if st.button("登录", key="btn_login"):
                res = st.session_state["user_service"].login(
                    login_user, login_pwd)
                if res["status"] == "success":
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = res["username"]
                    st.rerun()
                else:
                    st.error(res["message"])

        with tab2:
            reg_user = st.text_input("新用户名", key="reg_user")
            reg_pwd = st.text_input("新密码", type="password", key="reg_pwd")
            reg_pwd_confirm = st.text_input(
                "确认密码", type="password", key="reg_pwd_confirm")
            if st.button("注册", key="btn_reg"):
                if reg_pwd != reg_pwd_confirm:
                    st.error("两次密码不一致")
                elif not reg_user or not reg_pwd:
                    st.error("用户名和密码不能为空")
                else:
                    res = st.session_state["user_service"].register(
                        reg_user, reg_pwd)
                    if res["status"] == "success":
                        st.success("注册成功，请登录")
                    else:
                        st.error(res["message"])
    else:
        st.write(f"欢迎, **{st.session_state['username']}**")
        if st.button("退出登录"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            # 清除聊天相关的 session_state，防止串号
            if "messages" in st.session_state:
                del st.session_state["messages"]
            if "rag_service" in st.session_state:
                del st.session_state["rag_service"]
            st.rerun()

# --- 主页面：聊天界面 ---
if not st.session_state["logged_in"]:
    st.info("请在左侧登录或注册以开始对话")
else:
    current_user = st.session_state["username"]

    # 标题
    st.title(f" 用户{current_user}的专属智能客服")
    st.divider()

    # 初始化 RAG 服务 (单例)
    if "rag_service" not in st.session_state:
        st.session_state["rag_service"] = RagService()

    # 初始化前端显示用的消息列表
    # 注意：Key 依赖于 username，切换用户时会自动重新初始化
    if "messages" not in st.session_state or st.session_state.get("last_user") != current_user:
        st.session_state["last_user"] = current_user

        # 从 Redis 加载该用户的历史记录
        history_obj = get_redis_history(current_user)
        langchain_messages = history_obj.messages

        displayed_messages = []
        if not langchain_messages:
            displayed_messages.append(
                {"role": "assistant", "content": f"你好 {current_user}，有什么可以帮助你？"})
        else:
            for msg in langchain_messages:
                role = msg.type
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
                displayed_messages.append(
                    {"role": role, "content": msg.content})

        st.session_state["messages"] = displayed_messages

    # 渲染历史消息
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 处理用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 1. 显示用户消息
        st.session_state["messages"].append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 调用 RAG
        response_content = ""
        with st.chat_message("assistant"):
            with st.spinner("AI 思考中..."):
                try:
                    # 关键：config 中的 session_id 传入当前登录的用户名
                    session_config = {
                        "configurable": {
                            "session_id": current_user
                        }
                    }

                    res_stream = st.session_state["rag_service"].chain.stream(
                        {"input": prompt},
                        config=session_config
                    )

                    placeholder = st.empty()
                    full_response = ""
                    for chunk in res_stream:
                        if isinstance(chunk, str):
                            full_response += chunk
                        else:
                            full_response += str(chunk.content) if hasattr(
                                chunk, 'content') else str(chunk)
                        placeholder.markdown(full_response)

                    response_content = full_response

                except Exception as e:
                    response_content = f"发生错误: {str(e)}"
                    st.error(response_content)

        # 3. 显示 AI 回复并保存到 Session State
        st.session_state["messages"].append(
            {"role": "assistant", "content": response_content})
