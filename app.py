import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import SetupMaster, State

def render_sidebar() -> tuple[str, bool]:
    st.sidebar.title("Setup/PC Master")

    page = st.sidebar.radio("Navigation", ["Chat", "About"], index=0)

    st.sidebar.markdown("---")

    if st.sidebar.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.last_final_state = None
        st.rerun()

    st.sidebar.markdown("### Preferences")
    show_debug = st.sidebar.toggle("Show debug", value=False)

    api_key_input = st.sidebar.text_input(
        "OpenAI API key (optional)",
        type="password",
        value=st.session_state.get("openai_api_key", ""),
        help="If set, this overrides the value in Streamlit secrets for this browser session.",
    )
    if api_key_input:
        st.session_state.openai_api_key = api_key_input

    return page, show_debug

def main():
    page, show_debug = render_sidebar()

    if page == "About":
        st.title("About")
        st.markdown(
            """
This app is a chat assistant that helps with:
- PC build recommendations
- Room/desk setup recommendations
- Budget-based shopping suggestions

Use the **Chat** page to ask questions. Use the sidebar to clear chat or toggle debug.
"""
        )
        return

    st.title("Setup/PC Master")
    st.markdown("Ask me about a PC setup recommendations, Room setup recommendations, or a budget on either one!")


    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_final_state" not in st.session_state:
        st.session_state.last_final_state = None


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if show_debug and st.session_state.last_final_state is not None:
        with st.sidebar.expander("Debug info", expanded=False):
            st.json(st.session_state.last_final_state)


    if prompt := st.chat_input("What is on your room/PC To-Do List?"):
        st.session_state.messages.append({"role": "user", "content": prompt})


        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            try:

                api_key = st.session_state.get("openai_api_key") or st.secrets.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("Missing OpenAI API key. Add it in secrets or enter it in the sidebar.")

                agent = SetupMaster(api_key)


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
                st.session_state.last_final_state = final_state


                if final_state.get("responseToUser"):
                    response = final_state.get("responseToUser")
                    message_placeholder.markdown(response)


                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    message_placeholder.markdown("I'm sorry, I'm not sure how to help with that. Please try again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                message_placeholder.markdown("I'm sorry, something went wrong. Please try again.")

if __name__ == "__main__":
    main()
                