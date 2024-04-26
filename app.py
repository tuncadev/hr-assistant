import streamlit as st
import json

responses = st.session_state.get('responses', {})
selected_vacancy_value = responses.get("selected_vacancy", "")
with open('vacancies.json', 'r') as f:
    vacancies_data = json.load(f)
    vacancy_names = [vacancy['vacancy_name'] for vacancy in vacancies_data]
index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
    selected_vacancy_value)
responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
responses["email"] = st.text_input("E-Mail", value=responses.get("email", ""), key=f"email")
responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")



