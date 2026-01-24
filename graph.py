import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any, TypedDict, Annotated, Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from setup_agent import SetupAgent
from create_llm_message import create_llm_msg


class State(TypedDict):
    lnode: Optional[str]
    category: Optional[str]
    sessionHistory: List[BaseMessage]
    user_input: str
    responseToUser: Optional[str]


class Category(BaseModel):
    category: str

class SetupMaster():
    def __init__(self, api_key):
        model = st.secrets.get("model", "gpt-4o-mini")
        self.model = ChatOpenAI(model=model, api_key=api_key)


        self.setup_agent_class = SetupAgent(self.model)

        workflow = StateGraph(State)

        workflow.add_node("start", self.initial_classifier)
        workflow.add_node("setup", self.setup_agent)
        workflow.add_node("general", self.general_agent)

        workflow.add_edge(START, "start")
        workflow.add_conditional_edges(
            "start",
            self.route_to_agent,
            {
                "setup": "setup",
                "general": "general"
            }
        )
        workflow.add_edge("setup", END)
        workflow.add_edge("general", END)

        self.workflow = workflow.compile()



    def route_to_agent(self, state: State) -> str:
        """Route to the appropriate agent based on category."""
        category = state.get("category", "general")
        if category not in ["setup", "general"]:
            category = "general"
        return category



    def initial_classifier(self, state: State) -> State:
        """Classify the user input to determine which agent should handle it."""
        user_input = state["user_input"].lower().strip()
        session_history = state.get("sessionHistory", [])

        # Default
        category = "general"

        # Quick budget detection
        if "$" in user_input or "budget" in user_input:
            category = "setup"
        else:
            intro_keywords = [
                "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
                "who are you", "what are you", "introduce yourself", "tell me about yourself",
                "what can you do", "start", "begin", "howdy", "greetings", "yo", "sup"
            ]
            setup_keywords = ["setup", "build", "pc", "room", "desk", "table", "bed", "paint", "redo room", "parts"]
            setup_patterns = [
                "make me a setup", "tell me a color", "show me a desk", "redo room",
                "setup for my kid", "setup as a surprise", "setup for myself", "setup for my room",
                "setup for any", "painting my room", "secret room"
            ]

            if any(keyword in user_input for keyword in intro_keywords):
                category = "general"
            elif any(keyword in user_input for keyword in setup_keywords) or any(pattern in user_input for pattern in setup_patterns):
                category = "setup"
            elif len(user_input) <= 10 and session_history:
                # Fall back to last assistant/user content hints
                for msg in reversed(session_history):
                    if hasattr(msg, "content") and msg.content:
                        last_response = str(msg.content).lower()
                        if "setup" in last_response or "build" in last_response:
                            category = "setup"
                            break

        result_state = {
            **state,
            "category": category,
            "lnode": "initial_classifier"
        }
        return result_state

    def setup_agent(self, state: State) -> State:
        """Handle setup-related queries."""
        return self.setup_agent_class.setup_agent(state["user_input"], state.get("sessionHistory", []))


    def general_agent(self, state: State) -> State:
        """Handle general queries, but try to keep it on the topic of PC specs and room setup"""
        user_input = state["user_input"].lower()

        intro_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", 
                     "who are you", "what are you", "introduce yourself", "tell me about yourself",
                     "what can you do", "start", "begin"]

        is_intro = any(keyword in user_input for keyword in intro_keywords)

        if is_intro:
            response = """Hello! I am a: PC/Room setup master and expert!
            
            I specialize in helping you in 2 areas!:
            1. PC specs and builds
            2. Room setup and design
            How can I help you today?"
            """
        else:
            response = "I'm here to help with PC and room setups. Could you clarify your request?"

        return {
            "lnode": "general_agent",
            "responseToUser": response,
            "category": "general",
            "sessionHistory": state.get("sessionHistory", []),
            "user_input": state["user_input"],
        }


