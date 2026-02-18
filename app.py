import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import SetupMaster, State
import uuid
import re
import os
import pathlib


if not st.user.is_logged_in:
    st.info("Click below to log in with Google.")
    st.button("Login with Google", on_click=st.login, args=["google"])
    st.stop()





def _set_page(page: str) -> None:
    st.session_state.page = page

def _toggle_white_mode() -> None:
    """Toggle white mode on/off"""
    if "white_mode" not in st.session_state:
        st.session_state.white_mode = False
    st.session_state.white_mode = not st.session_state.white_mode

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

def admin_panel():
    if st.user.email == "ghostsnightmaref@gmail.com":
        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"]:has(> div#admin-panel-marker) .stButton > button {
                background: rgba(255,255,255,0.15) !important;
                color: #fbbf24 !important;
                border: 1px solid #fbbf24 !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }
            div[data-testid="stVerticalBlock"]:has(> div#admin-panel-marker) .stButton > button:hover {
                background: rgba(255,255,255,0.25) !important;
            }
            </style>
            <div id="admin-panel-marker"></div>
            """,
            unsafe_allow_html=True,
        )
        with st.container():
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #1e3a5f, #2d5986);
                            padding: 1.5rem 2rem; border-radius: 10px;
                            border-left: 4px solid #fbbf24;
                            margin-bottom: -1rem; min-height: 120px;">
                    <span style="font-size: 1.3rem; font-weight: 600; color: #fbbf24;">
                        Admin Panel!
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
           

def render_top_nav() -> str:
    st.success(f"Logged in as: {st.user.email}")
    st.button("Logout", on_click=st.logout)

    if "page" not in st.session_state:
        st.session_state.page = "Chat"
    if "white_mode" not in st.session_state:
        st.session_state.white_mode = False

    left, mid, _ = st.columns([1, 2, 1])
    with left:
        if st.button("⚙️", key="gear_button", help="Settings"):
            if "show_settings" not in st.session_state:
                st.session_state.show_settings = False
            st.session_state.show_settings = not st.session_state.show_settings
    
    # Show settings menu if toggled
    if st.session_state.get("show_settings", False):
        with st.expander("⚙️ Settings", expanded=True):
            if st.button("Setting 1: Toggle White Mode", key="setting1", use_container_width=True):
                _toggle_white_mode()
                st.session_state.show_settings = False
                st.rerun()
    
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

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e3a5f, #2d5986);
                    padding: 1rem 1.2rem; border-radius: 10px;
                    border-left: 3px solid #fbbf24;">
            <span style="font-size: 1rem; font-weight: 600; color: #fbbf24;">
                Need help?
            </span>
            <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                Message at <a href="mailto:ghostsnightmaref@gmail.com" style="color: #93c5fd; text-decoration: none;">ghostsnightmaref@gmail.com</a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def main():
    admin_panel()
    # Apply white mode CSS if enabled — polished light theme
    if st.session_state.get("white_mode", False):
        st.markdown("""
        <style>
        /* Base: soft off-white background */
        .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #fafbfc 0%, #f0f2f5 100%) !important;
        }
        .main .block-container {
            background: transparent !important;
            padding-top: 1.5rem !important;
        }
        /* Typography: readable dark gray */
        .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp span, .stApp div {
            color: #1a1d21 !important;
        }
        .stMarkdown { color: #1a1d21 !important; }
        /* Sidebar: subtle card-like panel */
        [data-testid="stSidebar"], .stSidebar {
            background: linear-gradient(180deg, #ffffff 0%, #f5f6f8 100%) !important;
            box-shadow: 2px 0 12px rgba(0,0,0,0.06) !important;
        }
        [data-testid="stSidebar"] .stMarkdown { color: #1a1d21 !important; }
        /* Buttons: clean and consistent */
        .stButton > button {
            background-color: #ffffff !important;
            color: #1a1d21 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        }
        .stButton > button:hover {
            background-color: #f3f4f6 !important;
            border-color: #9ca3af !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06) !important;
        }
        /* Primary (selected) buttons */
        .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border: none !important;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(180deg, #1d4ed8 0%, #1e40af 100%) !important;
        }
        /* Chat: user messages — soft blue */
        .stChatMessage[data-testid="user-message"] {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
            border: 1px solid #bfdbfe !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        /* Chat: assistant messages — soft gray */
        .stChatMessage[data-testid="assistant-message"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        /* Fallback for chat messages without data-testid */
        .stChatMessage {
            border-radius: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        /* Chat input */
        [data-testid="stChatInput"] {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        }
        /* Dividers */
        hr { border-color: #e5e7eb !important; opacity: 0.8; }
        /* Expander / settings panel */
        .streamlit-expanderHeader {
            background: #f8fafc !important;
            border-radius: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)

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
                