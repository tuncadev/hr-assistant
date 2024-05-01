import json
import os
import uuid
import streamlit as st
import time
from crewai import Agent, Task
from langchain_openai import ChatOpenAI

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


# App Start Function
def run():
    # Step 1: Get user and vacancy information
    if current_step == 1:
        # Set Defaults
        index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
            selected_vacancy_value)
        # Welcome
        msg = st.chat_message("adventurer-neutral", avatar=f"{assistant_avatar_path}")
        msg.html("<b>HYS-Assistant</b>: <i>Please fill in the form to  continue with your application.</i>")
        msg.html("<span style='color:#DB005F; font-weight:600;'><i>* All fields are required</i></span>")
        # The form
        responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
        responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")
        selected_vacancy = responses["selected_vacancy"]
        uploaded_file = st.file_uploader("Choose a file")
        responses["uploaded_file"] = uploaded_file
        # Buttons
        col1, col2 = st.columns([14, 3])
        # Initialize the form
        if col2.button("Next"):
            if are_all_fields_filled(responses) and uploaded_file:
                # Applicant  name
                name = responses["name"]
                msg = st.chat_message("assistant", avatar=f"{assistant_avatar_path}")
                msg.html(f"<b>HYS-Assistant</b>: {name}, <i>I am working on your resume. Please give me some time for analysis. This should not take long...</i>")
                # Loader
                with st.spinner("The assistant is working. Please stand by..."):
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
                st.rerun()
            else:
                st.warning("All fields are required. Please check the fields for errors.")
    # Step 2: Connect to gpt and execute "Cv Analysis" Task
    if current_step == 2:
        # Get Crew Data
        agent_data = GetAgentData()
        task_data = GetTaskData()
        # Applicant  name
        name = responses["name"]
        # Loader
        with st.spinner("The assistant is still working. Please stand by..."):
            with open(f"{temp_path}/resume.txt") as r:
                resume = r.read()
            with open(f"{temp_path}/vacancy.txt") as r:
                vacancy = r.read()
            # Get the cv analyst agent
            human_resources_manager = agent_data.return_human_resources_manager()
            # Get cv  analysis task
            human_resources_manager_task = task_data.return_task('Human Resources Manager', agent_instance=human_resources_manager, vac=f"{vacancy}", res=f"{resume}")
            # Execute the task
            fist_analysis = human_resources_manager_task.execute()
            with open(os.path.join(temp_path, "first_analysis.txt"), "w") as f:
                f.write("FIRST ANALYSIS:\n")
                f.write("----------------------------\n\n")
                f.write(fist_analysis)
                f.flush()
        st.session_state['current_step'] = current_step + 1
        st.rerun()
    # Step 3: Connect to gpt and execute "Generate Questions" Task
    if current_step == 3:
        # Get Crew Data
        agent_data = GetAgentData()
        task_data = GetTaskData()
        # Applicant name
        name = responses["name"]
        msg = st.chat_message("assistant", avatar=f"{assistant_avatar_path}")
        msg.html("<b>HYS-Assistant</b>: <i>Please give me some more time for analysis. We are almost there</i>")
        with open(f"{temp_path}/first_analysis.txt") as fr:
            first_analysis = fr.read()
        with st.spinner("The analysis is still running. Please stand by..."):
            recruitment_manager = agent_data.return_recruitment_manager()
            recruitment_manager_task = task_data.return_task('Recruitment Manager', agent_instance=recruitment_manager, first_analysis=first_analysis)
            questions = recruitment_manager_task.execute()
            with open(os.path.join(temp_path, "questions.json"), "w") as fq:
                fq.write(questions)
                fq.flush()
        st.session_state['current_step'] = current_step + 1
        st.rerun()
    # Step 4 - Display additional questions
    if current_step == 4:
        questions_path = f"{temp_path}/questions.json"
        if is_valid_json(questions_path):
            with open(questions_path) as q:
                questions = q.read()
            result_analysis_json = json.loads(questions)
            questions = result_analysis_json.get('questions', [])
            message = st.chat_message("assistant", avatar="🤖")
            message.write(
                f"*{'name'}*, **please answer these questions to better analyze your suitability for the vacancy:**")
            num_questions = len(questions)
            answers = st.session_state.get('answers', [''] * num_questions)
            question_step = st.session_state.get('question_step', 1)
            rerun_needed = False
            if num_questions > 5:
                if question_step == 1:
                    for i, question in enumerate(questions[:5]):
                        answers[i] = st.text_input(f"{i + 1}. {question}", value=answers[i], key=f"q_{i}")
                    col1, col2 = st.columns([12, 3])
                    col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
                                on_click=lambda: st.session_state.update({'current_step': 1}))
                    if col2.button("Next Questions"):
                        if all(answers[:5]):
                            st.session_state['answers'] = answers
                            st.session_state['question_step'] = question_step + 1
                            rerun_needed = True
                        else:
                            st.warning("Please answer all questions before proceeding.")
                elif question_step == 2:
                    for i, question in enumerate(questions[5:]):
                        answers[i + 5] = st.text_input(f"{i + 6}. {question}", value=answers[i + 5], key=f"q_{i + 5}")
                    col1, col2 = st.columns([11, 2])
                    if col1.button("Previous"):
                        st.session_state['answers'] = answers
                        st.session_state['question_step'] = 1
                        rerun_needed = True
                    elif col2.button("Continue"):
                        if all(answers[5:]):
                            st.session_state['answers'] = answers
                            with open(os.path.join(f"{temp_path}", "questions_answers.txt"),
                                      "w") as f:
                                f.write("QUESTIONS AND ANSWERS:\n")
                                f.write("----------------------------\n\n")
                                for q, a in zip(questions, answers):
                                    f.write(f"Question: {q}\nAnswer: {a}\n")
                            st.session_state['current_step'] = current_step + 1
                            rerun_needed = True
                        else:
                            st.warning("Please answer all questions before proceeding.")
            else:
                for i, question in enumerate(questions):
                    answers[i] = st.text_input(f"{i + 1}. {question}", value=answers[i], key=f"q_{i}")
                col1, col2 = st.columns([12, 3])
                col1.button("Previous", disabled=True, key='previous', help='Go to previous page',
                            on_click=lambda: st.session_state.update({'question_step': 1}))
                if col2.button("Continue"):
                    if all(answers):
                        with open(os.path.join(f"{temp_path}", "questions_answers.txt"),
                                  "w") as f:
                            for q, a in zip(questions, answers):
                                f.write(f"Q: {q}\nA: {a}\n\n")
                        st.session_state['answers'] = answers
                        st.session_state['current_step'] = current_step + 1
                        rerun_needed = True
                    else:
                        st.warning("Please answer all questions before proceeding.")
            if rerun_needed:
                st.rerun()

        else:
            # If there is an error with questions and/or if there are no questions, continue to final report
            with open(os.path.join(f"{temp_path}", "questions_answers.txt"), "w") as f:
                f.write(f"There were no additional questions to ask to the candidate or there was an error with questions file.")
            st.session_state['current_step'] = current_step + 1
            st.rerun()
    # Step 5 - Send all analysis for final  report
    if current_step == 5:
        # Get data from files
        with open(f"{temp_path}/vacancy.txt", "r") as vac, open(f"{temp_path}/resume.txt", "r") as res, open(f"{temp_path}/first_analysis.txt", "r") as fa, open(f"{temp_path}/questions_answers.txt", "r") as qa:
            vacancy = vac.read()
            resume = res.read()
            first_analysis = fa.read()
            questions_answers = qa.read()
        # Get Crew Data
        agent_data = GetAgentData()
        task_data = GetTaskData()
        # Applicant name
        name = responses["name"]
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
            st.write(final_report)
            with open(os.path.join(f"{temp_path}", "final_report.txt"), "w") as fr:
                fr.write(final_report)
        # AOK CONTINUE HERE

if __name__ == "__main__":
    # Set Defaults - THESE SHOULD BE IN AN INIT FUNCTION - FUTURE TASK!
    assistant_avatar_path = "media/svg/hys-assistant-avatar.svg"
    current_step = st.session_state.get('current_step', 1)
    responses = st.session_state.get('responses', {})
    selected_vacancy_value = responses.get("selected_vacancy", "")
    vacancy_data = GetVacData()
    vacancy_headers = vacancy_data.sheet_headers()
    vacancy_names = vacancy_data.get_vacancy_names()
    # Set the temp path
    # Temp folder
    temp_path = get_temp_path()
    run()