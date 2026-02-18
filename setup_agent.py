import streamlit as st
from langchain_core.messages import SystemMessage, BaseMessage
from create_llm_message import create_llm_msg


class SetupAgent():
    def __init__(self, model):
        self.model = model
        self.system_prompt = """
        You are a computer expert and master.
        You will be given a user input and a session history.
        1. You will need to determine if the user is asking about a room setup or a PC build.
        2. If they give a budget, you will need to determine products that match the budget.
        3. If they give a specific PC build, you will need to determine products that match the build.
        4. You will need to return a list of products that match the user's request.
        5. If they do not give a room setup, pc build or budget, check the session history and match it up, if it does not match up, ask them for clarification.
        6. When recommending PC parts or products, ALWAYS include a direct purchase link for each item. Use Amazon search URLs in this format: https://www.amazon.com/s?k=PRODUCT+NAME (replace spaces with +). For example, for an "AMD Ryzen 5 7600X", link to https://www.amazon.com/s?k=AMD+Ryzen+5+7600X. Format each product as: **Product Name** — $Price — [Buy on Amazon](link). This makes it easy for the user to find and purchase the parts.
        """
        self.sessionHistory = []

    def get_response(self, user_input: str):
        msg = create_llm_msg(self.system_prompt, self.sessionHistory)
        llm_response = self.model.invoke(msg)

        return llm_response

    def setup_agent(self, user_input: str, session_history=None):
        if session_history is None:
            session_history = []



        from langchain_core.messages import HumanMessage


        messages = []
        messages.append(SystemMessage(content=self.system_prompt))
        messages.extend(session_history)
        messages.append(HumanMessage(content=user_input))

        llm_response = self.model.invoke(messages)

        return {
            "lnode": "setup_agent",
            "responseToUser": llm_response.content,
            "category": "setup",
            "sessionHistory": session_history,
            "user_input": user_input,
        }