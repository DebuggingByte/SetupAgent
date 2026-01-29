import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import SetupMaster, State
import uuid
import re

def _set_page(page: str) -> None:
    st.session_state.page = page

def _ensure_chat_state() -> None:
    """
    Multi-chat model:
    - st.session_state.chats: list[{"id": str, "title": str, "messages": list[dict]}]
    - st.session_state.active_chat_id: str

    Migrates legacy st.session_state.messages into the first chat if present.
    """
    if "chats" not in st.session_state:
        st.session_state.chats = []

    # Track how many "New chat N" threads we've created so far.
    # This keeps numbering stable across reruns within the session.
    if "new_chat_counter" not in st.session_state:
        max_n = 0
        for c in st.session_state.chats:
            t = str(c.get("title", "")).strip()
            m = re.fullmatch(r"New chat\s+(\d+)", t, flags=re.IGNORECASE)
            if m:
                try:
                    max_n = max(max_n, int(m.group(1)))
                except ValueError:
                    pass
        st.session_state.new_chat_counter = max_n

    # Migrate legacy single-chat state if it exists
    if "messages" in st.session_state and st.session_state.get("messages"):
        if not st.session_state.chats:
            chat_id = uuid.uuid4().hex
            st.session_state.chats.append(
                {"id": chat_id, "title": "New chat", "messages": list(st.session_state.messages)}
            )
            st.session_state.active_chat_id = chat_id
        del st.session_state["messages"]

    if "active_chat_id" not in st.session_state or not st.session_state.active_chat_id:
        if st.session_state.chats:
            st.session_state.active_chat_id = st.session_state.chats[0]["id"]
        else:
            chat_id = uuid.uuid4().hex
            st.session_state.chats.append({"id": chat_id, "title": "New chat", "messages": []})
            st.session_state.active_chat_id = chat_id

def _get_active_chat() -> dict:
    _ensure_chat_state()
    for c in st.session_state.chats:
        if c["id"] == st.session_state.active_chat_id:
            return c
    # If the active chat was removed somehow, fall back to first.
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]
    return st.session_state.chats[0]

def _set_active_chat(chat_id: str) -> None:
    st.session_state.active_chat_id = chat_id

def _new_chat() -> None:
    _ensure_chat_state()
    chat_id = uuid.uuid4().hex
    st.session_state.new_chat_counter = int(st.session_state.get("new_chat_counter", 0)) + 1
    st.session_state.chats.insert(
        0,
        {"id": chat_id, "title": f"New chat {st.session_state.new_chat_counter}", "messages": []},
    )
    st.session_state.active_chat_id = chat_id

def _delete_chat(chat_id: str) -> None:
    _ensure_chat_state()
    st.session_state.chats = [c for c in st.session_state.chats if c["id"] != chat_id]
    if not st.session_state.chats:
        # Always keep at least one chat available.
        new_id = uuid.uuid4().hex
        st.session_state.chats.append({"id": new_id, "title": "New chat", "messages": []})
        st.session_state.active_chat_id = new_id
    elif st.session_state.active_chat_id == chat_id:
        st.session_state.active_chat_id = st.session_state.chats[0]["id"]

def _maybe_update_chat_title(chat: dict) -> None:
    # If it's still a generic "New chat" (or "New chat N"), rename based on first user message.
    if not chat.get("messages"):
        return
    title = (chat.get("title") or "").strip()
    if title.lower() != "new chat" and not title.lower().startswith("new chat "):
        return
    for m in chat["messages"]:
        if m.get("role") == "user" and m.get("content"):
            raw = str(m["content"]).strip().replace("\n", " ")
            chat["title"] = (raw[:28] + "…") if len(raw) > 29 else raw
            return

def render_top_nav() -> str:
    if "page" not in st.session_state:
        st.session_state.page = "Chat"

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        b1, b2 = st.columns(2)
        with b1:
            st.button(
                "Chat",
                key="nav_chat",
                use_container_width=True,
                on_click=_set_page,
                args=("Chat",),
                type="primary" if st.session_state.page == "Chat" else "secondary",
            )
        with b2:
            st.button(
                "About",
                key="nav_about",
                use_container_width=True,
                on_click=_set_page,
                args=("About",),
                type="primary" if st.session_state.page == "About" else "secondary",
            )

    st.divider()
    return st.session_state.page

def render_sidebar() -> None:
    st.sidebar.title("Setup/PC Master")
    st.sidebar.markdown("---")

    _ensure_chat_state()

    st.sidebar.button("New chat", use_container_width=True, on_click=_new_chat)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Saved chats")
    # Render most recent first, with buttons for quick switching and delete buttons.
    for chat in st.session_state.chats:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.button(
                chat.get("title", "Chat"),
                key=f"chat_select_{chat['id']}",
                use_container_width=True,
                on_click=_set_active_chat,
                args=(chat["id"],),
                type="primary" if chat["id"] == st.session_state.active_chat_id else "secondary",
            )
        with col2:
            if st.button("🗑️", key=f"chat_delete_{chat['id']}", help="Delete chat"):
                _delete_chat(chat["id"])
                st.rerun()

def main():
    render_sidebar()
    page = render_top_nav()

    if page == "About":
        st.title("About")
        st.markdown(
            """
This app is a chat assistant that helps with:
- PC build recommendations
- Room/desk setup recommendations
- Budget-based shopping suggestions

Use the **Chat** page to ask questions. Use the sidebar to clear chat.
"""
        )
        return

    st.title("Setup/PC Master")
    st.markdown("Ask me about a PC setup recommendations, Room setup recommendations, or a budget on either one!")

    active_chat = _get_active_chat()
    for message in active_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is on your room/PC To-Do List?"):
        active_chat["messages"].append({"role": "user", "content": prompt})
        _maybe_update_chat_title(active_chat)


        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            try:

                if "OPENAI_API_KEY" not in st.secrets:
                    raise ValueError("Missing OpenAI API key. Add `OPENAI_API_KEY` to Streamlit secrets.")

                agent = SetupMaster(st.secrets["OPENAI_API_KEY"])


                session_history = []
                for msg in active_chat["messages"][:-1]:
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
                    response = final_state.get("responseToUser")
                    message_placeholder.markdown(response)


                    active_chat["messages"].append({"role": "assistant", "content": response})
                else:
                    message_placeholder.markdown("I'm sorry, I'm not sure how to help with that. Please try again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                message_placeholder.markdown("I'm sorry, something went wrong. Please try again.")

if __name__ == "__main__":
    main()
                