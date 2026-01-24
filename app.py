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

            try:

                agent = SetupMaster(st.secrets["OPEN_API_KEY"])


                session_history = []
                for msg in st.session_state.messages[:-1]:
                    if msg["role"] == "user":
                        session_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        session_history.append(AIMessage(content=msg["content"]))
                

                initial_state: State = {
                    "user_input": prompt,
                    "sessionHistory": session_history,
                    "lnode": "None",
                    "category": None,
                    "responseToUser": None,
                }



                final_state = agent.workflow.invoke(initial_state)


                if final_state.get("responseToUser"):
                    response = final_state.get["responseToUser"]
                    message_placeholder.markdown(response)


                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    message_placeholder.markdown("I'm sorry, I'm not sure how to help with that. Please try again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                message_placeholder.markdown("I'm sorry, something went wrong. Please try again.")

if __name__ == "__main__":
    main()
                