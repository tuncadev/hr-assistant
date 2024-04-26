import os
import uuid
import streamlit as st
import json
from tools.read_file import ReadFileContents

def get_temp_path():
    if 'temp_path' not in st.session_state:
        temp_name = str(uuid.uuid4())
        temp_path = f"temp/{temp_name}"
        os.makedirs(temp_path, exist_ok=True)
        st.session_state['temp_path'] = temp_path
    return st.session_state['temp_path']


def are_all_fields_filled(responses):
    for key, value in responses.items():
        if not value:
            return False
    return True


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



