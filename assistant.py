import json
import os
import time
import uuid
import streamlit as st

#Tools
from tools.getvacancies import GetVacData
from tools.read_file import ReadFileContents
from tools.get_tasks import GetTaskData
from tools.get_agents import GetAgentData
from tools.db_connect import DBConnect


# App functions start #
# Check if all fields are filled
def are_all_fields_filled(responses):
    for key, value in responses.items():
        if not value:
            return False
    return True

# Check uploaded file and retrieve text
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


def is_valid_json(file_path):
    try:
        with open(file_path) as file:
            data = file.read().strip()
            # Check if the data can be loaded as JSON and starts with '{' (object)
            json.loads(data)
            return data.startswith('{')
    except (json.JSONDecodeError, FileNotFoundError):
        return False
# App functions end #


def run():
    if current_step == 1:
        st.session_state['current_step'] = 1
        hys_form = st.empty()
        with hys_form.form("user_information"):
            # Set Defaults
            index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
                selected_vacancy_value)
            # Welcome
            msg = st.chat_message("adventurer-neutral", avatar=f"{assistant_avatar_path}")
            msg.html("<b>HYS-Assistant</b>: <i>Please fill in the form to  continue with your application.</i>")
            msg.html("<span style='color:#DB005F; font-weight:600;'><i>* All fields are required</i></span>")
            # The form
            responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
            responses["email"] = st.text_input("E-mail", value=responses.get("email", ""), key=f"email")
            responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")
            uploaded_file = st.file_uploader("Choose a file")
            submit = st.form_submit_button("Continue", use_container_width=True, type="secondary")
            if submit:
                if are_all_fields_filled(responses) and uploaded_file:
                    cv_contents = check_uploaded_file(uploaded_file)
                    formatter = agent_data.return_document_expert()
                    formatter_task = task_data.return_task("Document Expert", agent_instance=formatter, res=cv_contents)
                    new_resume = formatter_task.execute()
                    with DBConnect() as db:
                        name = responses["name"]
                        email = responses["email"]
                        selected_vac_name = responses["selected_vacancy"]
                        selected_vac_details = db.get_vac_details(selected_vac_name)
                        selected_vac_details = json.dumps(selected_vac_details)
                        applicant_key = db.create_temp(name=name,
                                                       email=email,
                                                       selected_vac_name=selected_vac_name,
                                                       selected_vac_details=selected_vac_details)
                        responses["temp_path"] = applicant_key
                        if uploaded_file is not None:
                            # Get cv contents
                            cv_contents = check_uploaded_file(uploaded_file)
                            # Reformat using agent
                            formatter = agent_data.return_document_expert()
                            formatter_task = task_data.return_task("Document Expert", agent_instance=formatter, res=cv_contents)
                            new_resume = formatter_task.execute()
                            # Insert into DB CV content
                            db.insert_into_resumes(applicant_key, content=new_resume)
                    # Set Session responses
                    st.session_state['responses'] = responses
                    # Goto next step
                    st.session_state['current_step'] = current_step + 1
                    hys_form.empty()
                else:
                    st.warning("All fields are required. Please check the fields for errors.")
    if 'current_step' in st.session_state:
        step = st.session_state['current_step']
        if step == 2:
            applicant_key = responses["temp_path"]
            # Applicant  name
            with DBConnect() as db:
                name = db.get_applicant_name(applicant_key)
                vacancy = db.get_selected_vac_details(applicant_key=applicant_key)
                resume = db.select_from_resumes(applicant_key=applicant_key)
            with st.spinner("Now, the HR Manager is analyzing your resume. Please stand by..."):
                # Get the cv analyst agent
                human_resources_manager = agent_data.return_human_resources_manager()
                # Get cv  analysis task
                human_resources_manager_task = task_data.return_task('Human Resources Manager',
                                                                     agent_instance=human_resources_manager,
                                                                     vac=f"{vacancy}", res=f"{resume}")
                first_analysis = human_resources_manager_task.execute()
                with DBConnect() as db:
                    db.insert_into_reports(applicant_key=applicant_key, report_table="first_analysis", content=first_analysis)
            with st.spinner("Now, the HR Manager is analyzing your resume. Please stand by..."):


if __name__ == "__main__":
    with st.spinner("Initializing, please wait..."):
        # Set Defaults - THESE SHOULD BE IN AN INIT FUNCTION - FUTURE TASK!
        current_step = st.session_state['current_step'] if 'current_step' in st.session_state else 1
        assistant_avatar_path = "media/svg/hys-assistant-avatar.svg"
        responses = st.session_state.get('responses', {})
        selected_vacancy_value = responses.get("selected_vacancy", "")
        vacancy_data = GetVacData()
        agent_data = GetAgentData()
        task_data = GetTaskData()
        init_vacancies = vacancy_data.init_vacancies()
        if init_vacancies:
            with DBConnect() as db:
                vacancy_names = db.get_vacancy_names()
        run()


