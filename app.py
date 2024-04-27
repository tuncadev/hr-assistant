import json
import os
import uuid
import streamlit as st
from tools.read_file import ReadFileContents


def get_temp_path():
    if 'temp_path' not in st.session_state:
        temp_name = str(uuid.uuid4())
        temp_path = f"temp/{temp_name}"
        os.makedirs(temp_path, exist_ok=True)
        st.session_state['temp_path'] = temp_path
    return st.session_state['temp_path']


def check_uploaded_file(uploaded_file):
    file_name = uploaded_file.name
    file_content = uploaded_file.getvalue()
    readfile = ReadFileContents(file_name, file_content)
    if file_name.endswith('.doc'):
        cv_content = readfile.read_doc_file()
    elif file_name.endswith('.docx'):
        cv_content = readfile.read_docx_file()
    elif file_name.endswith('.txt'):
        cv_content = readfile.read_txt_file()
    elif file_name.endswith('.pdf'):
        cv_content = readfile.read_pdf_file()
    else:
        cv_content = "Unsupported file type"
    return cv_content


def query_init(selected_vacancy, cv_contents, vacancy_details):
    agent_analysis = "Agent analysis (%)"
    information_found = "why"
    requirement_match = []
    would_be_plus_match = []

    for requirement in selected_vacancy["vacancy_requirements"][0]["vacancy_requirements_description"]:
        requirement_match.append(f"Requirement: {requirement}\n "
                                 f"Agent analysis: {agent_analysis} \n"
                                 f"{information_found} \n\n")
    for would_be_plus in selected_vacancy["would_be_plus"][0]["would_be_plus_description"]:
        would_be_plus_match.append(f"Would be plus: {would_be_plus}\n"
                                   f"Agent analysis: {agent_analysis} \n"
                                   f"{information_found} \n\n")

    requirement_match = "\n".join(requirement_match)
    would_be_plus_match = "\n".join(would_be_plus_match)
    expected_output = (f"\nVacancy name: {selected_vacancy['vacancy_name']} \n"
                       f"Candidate Suitability Percentage: {agent_analysis}\n"
                       f"Candidate requirements match: \n\n "
                       f"{requirement_match}\n\n"
                       f"Candidate would-be-plus match: \n\n"
                       f"{would_be_plus_match}\n")
    inputs = {
        "vacancy": f"{vacancy_details}",
        "resume": f"{cv_contents}",
        "expected_output": f"{expected_output}"
    }
    return inputs


def are_all_fields_filled(responses):
    for key, value in responses.items():
        if not value:
            return False
    return True


current_step = st.session_state.get('current_step', 1)
responses = st.session_state.get('responses', {})
selected_vacancy_value = responses.get("selected_vacancy", "")

st.write = selected_vacancy_value

with open('vacancies.json', 'r') as f:
    vacancies_data = json.load(f)
    vacancy_names = [vacancy['vacancy_name'] for vacancy in vacancies_data]
index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
    selected_vacancy_value)
responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
responses["email"] = st.text_input("E-Mail", value=responses.get("email", ""), key=f"email")
responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")
uploaded_file = st.file_uploader("Choose a file")
col1, col2 = st.columns([12, 3])
col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
            on_click=lambda: st.session_state.update({'current_step': 1}))
if col2.button("Next"):
    if are_all_fields_filled(responses) and uploaded_file:
        st.session_state['responses'] = responses
        with st.spinner("The assistant is analyzing the details of your CV, please wait..."):
            if uploaded_file is not None:
                cv_contents = check_uploaded_file(uploaded_file)  # operation that takes time
                temp_path = get_temp_path()
                with open(os.path.join(temp_path, "resume.txt"), "w") as f:
                    f.write(cv_contents)
        st.session_state['current_step'] = 2
        st.rerun()
    else:
        st.warning("All fields are required. Please check the fields for errors.")
