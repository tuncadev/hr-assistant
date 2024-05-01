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


# App functions start #
# Check if all fields are filled
def are_all_fields_filled(responses):
    for key, value in responses.items():
        if not value:
            return False
    return True


# Create a temp folder
def get_temp_path():
    if 'temp_path' not in st.session_state:
        temp_name = str(uuid.uuid4())
        temp_path = f"temp/{temp_name}"
        os.makedirs(temp_path, exist_ok=True)
        st.session_state['temp_path'] = temp_path
    return st.session_state['temp_path']


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


# Set the temp path
# Temp folder



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
            responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index,
                                                         key="selected_vacancy")
            uploaded_file = st.file_uploader("Choose a file")
            submit = st.form_submit_button("Continue", use_container_width=True, type="secondary")

            if submit:
                temp_path = get_temp_path()
                responses["uploaded_file"] = uploaded_file
                if are_all_fields_filled(responses) and uploaded_file:
                    uploaded_file = responses["uploaded_file"]
                    # Read the resume file
                    if uploaded_file is not None:
                        cv_contents = check_uploaded_file(uploaded_file)  # operation that takes time
                        with open(os.path.join(temp_path, "resume.txt"), "w") as f:
                            f.write("RESUME:\n")
                            f.write("----------------------------\n\n")
                            f.write(cv_contents)
                    # Get the selected vacancy details
                    if vacancy_headers:
                        selected_vacancy = responses["selected_vacancy"]
                        vacancy_details = vacancy_data.get_selected_vacancy_details(selected_vacancy)
                        with open(os.path.join(temp_path, "vacancy.txt"), "w") as f:
                            f.write("VACANCY DETAILS:\n")
                            f.write("----------------------------\n\n")
                            f.write(vacancy_details)
                            f.flush()
                    else:
                        vacancy_details = "Vacancy not found"
                        with open(os.path.join(temp_path, "vacancy.txt"), "w") as f:
                            f.write("VACANCY DETAILS:\n")
                            f.write("----------------------------\n\n")
                            f.write(vacancy_details)
                            f.flush()
                    # Set Session responses
                    st.session_state['responses'] = responses
                    # Goto next step
                    st.session_state['current_step'] = current_step + 1
                    hys_form.empty()
                else:
                    st.warning("All fields are required. Please check the fields for errors.")

    if all(key in st.session_state for key in ['current_step', 'temp_path']):
        step = st.session_state['current_step']
        # Temp path
        temp_path = st.session_state['temp_path']
        if step == 2:
            # Applicant  name
            name = responses["name"]
            msg = st.empty()
            msg.chat_message("assistant", avatar=assistant_avatar_path)
            msg.write(f"{name}, Please wait while we analyze your resume. This won't take long...")
            # Get Crew Data
            agent_data = GetAgentData()
            task_data = GetTaskData()
            with open(f"{temp_path}/resume.txt") as r:
                resume = r.read()
            with open(f"{temp_path}/vacancy.txt") as r:
                vacancy = r.read()
            # Get the cv analyst agent
            human_resources_manager = agent_data.return_human_resources_manager()
            # Get cv  analysis task
            human_resources_manager_task = task_data.return_task('Human Resources Manager',
                                                                 agent_instance=human_resources_manager,
                                                                 vac=f"{vacancy}", res=f"{resume}")
            # Loader
            with st.spinner("The HR Manager is analyzing your resume. Please stand by..."):
                # Execute the task
                first_analysis = human_resources_manager_task.execute()
                with open(os.path.join(temp_path, "first_analysis.txt"), "w") as f:
                    f.write("FIRST ANALYSIS:\n")
                    f.write("----------------------------\n\n")
                    f.write(first_analysis)
                    f.flush()
            with st.spinner("Now, the Recruitment Manager is getting ready for the interview. Please stand by..."):
                recruitment_manager = agent_data.return_recruitment_manager()
                recruitment_manager_task = task_data.return_task('Recruitment Manager',
                                                                 agent_instance=recruitment_manager,
                                                                 first_analysis=first_analysis)
                # Execute the task
                questions = recruitment_manager_task.execute()
                with open(os.path.join(temp_path, "questions.json"), "w") as fq:
                    fq.write(questions)
                    fq.flush()
            step = step + 1
            msg.empty()
            st.session_state['current_step'] = step
        if step == 3:
            questions_path = f"{temp_path}/questions.json"
            if is_valid_json(questions_path):
                with open(questions_path) as q:
                    questions = q.read()
                result_analysis_json = json.loads(questions)
                questions = result_analysis_json.get('questions', [])
                num_questions = len(questions)
                answers = st.session_state.get('answers', [''] * num_questions)
                # Applicant  name
                name = responses["name"]
                message = st.chat_message("assistant", avatar=f"{assistant_avatar_path}")
                message.write(
                    f"*{name}*, **please answer these questions to better analyze your suitability for the vacancy:**")
                if len(questions) <= 5:
                    q_form_1 = st.empty()
                    with q_form_1.form("Questions"):
                        for i, question in enumerate(questions):
                            answers[i] = st.text_input(question, key=f"q_{i}")
                        submit = st.form_submit_button("Continue", use_container_width=True, type="secondary")
                        if submit:
                            if all(answers):
                                st.session_state['answers'] = answers
                                with open(os.path.join(f"{temp_path}", "questions_answers.txt"),
                                          "w") as f:
                                    f.write("QUESTIONS AND ANSWERS:\n")
                                    f.write("----------------------------\n\n")
                                    for q, a in zip(questions, answers):
                                        f.write(f"Question: {q}\nAnswer: {a}\n")
                                step = step + 1
                                st.session_state['current_step'] = step
                                q_form_1.empty()
                            else:
                                st.warning("Please answer all questions before proceeding.")
                elif len(questions) > 5:
                    q_form_2 = st.empty()
                    st.markdown(
                        """
                        <style>
                        [data-testid="stAppViewBlockContainer"] {
                            max-width: 1200px;
                            margin:auto;
                        }
                        </style>
                        """, unsafe_allow_html=True
                    )
                    with q_form_2.form("Questions"):
                        col1, col2 = st.columns(2, gap="medium")  # Create two columns
                        for i, question in enumerate(questions):
                            if i < len(questions) // 2:  # Distribute questions between columns
                                answers[i] = col1.text_input(question, key=f"q_{i}")
                            else:
                                answers[i] = col2.text_input(question, key=f"q_{i}")
                        submit = st.form_submit_button("Continue", use_container_width=True, type="secondary")
                        if submit:
                            if all(answers):
                                st.session_state['answers'] = answers
                                with open(os.path.join(f"{temp_path}", "questions_answers.txt"),
                                          "w") as f:
                                    f.write("QUESTIONS AND ANSWERS:\n")
                                    f.write("----------------------------\n\n")
                                    for q, a in zip(questions, answers):
                                        f.write(f"Question: {q}\nAnswer: {a}\n")
                                q_form_2.empty()
                                step = step + 1
                                st.session_state['current_step'] = step

                            else:
                                st.warning("Please answer all questions before proceeding.")
            else:
                # If there is an error with questions and/or if there are no questions, continue to final report
                with open(os.path.join(f"{temp_path}", "questions_answers.txt"), "w") as f:
                    f.write("QUESTIONS AND ANSWERS:\n")
                    f.write("----------------------------\n\n")
                    f.write(f"There were no additional questions to ask to the candidate or there was an error with questions file.")
                step = step + 1
                st.session_state['current_step'] = step
        if step == 4:
            with open(f"{temp_path}/vacancy.txt", "r") as vac, open(f"{temp_path}/resume.txt", "r") as res, open(f"{temp_path}/first_analysis.txt", "r") as fa, open(f"{temp_path}/questions_answers.txt", "r") as qa:
                vacancy = vac.read()
                resume = res.read()
                first_analysis = fa.read()
                questions_answers = qa.read()
            # Get Crew Data
            agent_data = GetAgentData()
            task_data = GetTaskData()
            # Send all to agent for analysis
            with st.spinner("Final analysis"):
                hr_director = agent_data.return_human_resources_director()
                hr_director_task = task_data.return_task(
                    'Human Resources Director',
                    agent_instance=hr_director,
                    vac=vacancy,
                    res=resume,
                    first_analysis=first_analysis,
                    questions_answers=questions_answers
                )
                final_report = hr_director_task.execute()
                with open(os.path.join(f"{temp_path}", "final_report.txt"), "w") as fr:
                    fr.write(final_report)
                    fr.flush()
                step = step + 1
                st.session_state['current_step'] = step
        if step == 5:
            # Get Crew Data
            agent_data = GetAgentData()
            task_data = GetTaskData()
            with open(f"{temp_path}/vacancy.txt", "r") as vac, open(f"{temp_path}/resume.txt", "r") as res, open(f"{temp_path}/first_analysis.txt", "r") as fa, open(f"{temp_path}/questions_answers.txt", "r") as qa, open(f"{temp_path}/final_report.txt") as fr:
                vacancy = vac.read()
                resume = res.read()
                first_analysis = fa.read()
                questions_answers = qa.read()
                final_report = fr.read()
            chief_of_hr = agent_data.return_chief_of_hr()
            chief_of_hr_task = task_data.return_task(
                'Chief of Human Resources Officer',
                agent_instance=chief_of_hr,
                vac=vacancy,
                res=resume,
                first_analysis=first_analysis,
                questions_answers=questions_answers,
                final_report=final_report
            )
            chief_of_hr_report = chief_of_hr_task.execute()
            with open(os.path.join(f"{temp_path}", "chief_of_hr_report.txt"), "w") as fr:
                fr.write(chief_of_hr_report)
                fr.flush()
            st.write(temp_path)
            st.write("All Done!")
            st.stop()

if __name__ == "__main__":
    # Set Defaults - THESE SHOULD BE IN AN INIT FUNCTION - FUTURE TASK!
    current_step = st.session_state['current_step'] if 'current_step' in st.session_state else 1
    assistant_avatar_path = "media/svg/hys-assistant-avatar.svg"
    responses = st.session_state.get('responses', {})
    selected_vacancy_value = responses.get("selected_vacancy", "")
    vacancy_data = GetVacData()
    vacancy_headers = vacancy_data.sheet_headers()
    vacancy_names = vacancy_data.get_vacancy_names()
    run()
