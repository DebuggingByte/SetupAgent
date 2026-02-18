import streamlit as st

st.set_page_config(page_title="Auth Test", page_icon="🔑")

st.title("Google Auth Test")

if not st.user.is_logged_in:
    st.info("Click below to log in with Google.")
    st.button("Login with Google", on_click=st.login, args=["google"])
    st.stop()

st.success(f"Logged in as: {st.user.email}")
st.button("Logout", on_click=st.logout)
