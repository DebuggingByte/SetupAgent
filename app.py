import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import SetupMaster, State

def main():
    st.title("Setup/PC Master")
    st.markdown("Ask me about a PC setup recommendations, Room setup recommendations, or a budget on either one!")


    if "messages" not in st.session_state:
        st.session_state.messages = []


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    if prompt := st.chat_input("What is on your room/PC To-Do List?"):
        st.session_state.messages.append({"role": "user", "content": prompt})


        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):
            message_placeholder = st.empty()
