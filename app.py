import os
import streamlit as st
from crewai import Agent, Task
from langchain_openai import ChatOpenAI

openai_api = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = str(openai_api)

agent = Agent(
    role='A Friend',
    goal='Just answer the question',
    backstory='You are an experienced psychologist, and your goal is to cheer people up',
    allow_delegation=False,
    verbose=True,
    llm=ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.3
    )
)


prompt = st.chat_input("Say something")
if prompt:
    task = Task(
        description=f"{prompt}",
        expected_output=f"Answer the question",
        agent=agent,
    )
    answer = task.execute()
    with st.chat_message("assistant"):
        st.write(answer)
