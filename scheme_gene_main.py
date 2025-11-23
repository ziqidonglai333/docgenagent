import streamlit as st
st.markdown("# 专业报告生成主页登录")
st.sidebar.markdown("# 专业报告生成主页登录")




def check_credentials(username, password):
    return username == "admin" and password == "admin"  # 这里硬编码了用户名和密码

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    username = st.text_input("用户名")
    password = st.text_input("密码", type='password')
    if st.button('登录'):
        if check_credentials(username, password):
            st.session_state.logged_in = True
            st.success("登录成功！")
        else:
            st.error("用户名或密码错误")
else:
    # 在这里放置你的 Streamlit 应用代码
    if st.button('登出'):
        st.session_state.logged_in = False