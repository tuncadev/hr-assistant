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

# OpenAI Environment
openai_api = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = str(openai_api)
open_llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.1
)


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


##############################################

##############################################
def hr_dep_manager():
    return Agent(
        role='Human Resources General Manager',
        goal="""
            * Read vacancy details.
            * Read the first analysis report of a resume.
            * Read the resume details. 
            * Read the additional questions and answers of the candidate from the interview.
            * Read the final report about the candidate. How suitable he is for the position. 
            * Pay attention to vacancy requirements and how well the candidate fills the requirements.
            * Analyze how well the other Human Resources agents worked, and how well their responsibilities were fulfilled.
            * Write a general report on the Human Resources Agents work.
            * If there are improvements to be made, clarify them professionally and detailed.
              """,
        backstory="""
              You are an extremely professional, very experienced  Senior Human Resources General Manager. 
              You have 25+ years of experience in job interviews and resume reviewing. 
              Your responsibility is to control the work of all Human Resources Agents.
              How well the task are being executed. 
              What should be improved, what should be preserved.
              """,
        allow_delegation=False,
        verbose=True,
        llm=open_llm
    )


# Set Defaults - THESE SHOULD BE IN AN INIT FUNCTION - FUTURE TASK!
assistant_avatar_path = "media/svg/hys-assistant-avatar.svg"
current_step = st.session_state.get('current_step', 1)
responses = st.session_state.get('responses', {})
selected_vacancy_value = responses.get("selected_vacancy", "")
# Set the temp path

# Step 1: Get user and vacancy information
if current_step == 1:
    # Set Defaults
    vacancy_data = GetVacData()
    vacancy_headers = vacancy_data.sheet_headers()
    vacancy_names = vacancy_data.get_vacancy_names()
    index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
        selected_vacancy_value)
    temp_path = get_temp_path()
    # Welcome
    msg = st.chat_message("adventurer-neutral", avatar=f"{assistant_avatar_path}")
    msg.html("<b>HYS-Assistant</b>: <i>Please fill in the form to  continue with your application.</i>")
    msg.html("<span style='color:#DB005F; font-weight:600;'><i>* All fields are required</i></span>")
    # The form
    responses["name"] = st.text_input("Name", value=responses.get("name", ""), key=f"name")
    responses["selected_vacancy"] = st.selectbox('Select a vacancy', vacancy_names, index=index, key="selected_vacancy")
    selected_vacancy = responses["selected_vacancy"]
    uploaded_file = st.file_uploader("Choose a file")
    # Buttons
    col1, col2 = st.columns([14, 3])
    # Initialize the form
    if col2.button("Next"):
        if are_all_fields_filled(responses) and uploaded_file:
            # Set Session responses
            st.session_state['responses'] = responses
            # Loader
            with st.spinner("The assistant is analyzing the details of your CV, please wait..."):
                # Read the resume file
                if uploaded_file is not None:
                    cv_contents = check_uploaded_file(uploaded_file)  # operation that takes time
                    with open(os.path.join(temp_path, "resume.txt"), "w") as f:
                        f.write("RESUME:\n")
                        f.write("----------------------------\n\n")
                        f.write(cv_contents)
                # Get the selected vacancy details
                if vacancy_headers:
                    vacancy_details = vacancy_data.get_selected_vacancy_details(selected_vacancy)
                    with open(os.path.join(temp_path, "vacancy.txt"), "w") as f:
                        f.write("VACANCY DETAILS:\n")
                        f.write("----------------------------\n\n")
                        f.write(vacancy_details)
                        f.flush()
                else:
                    vacancy_details = "Vacancy not found"
            st.session_state['current_step'] = current_step + 1
            st.rerun()
        else:
            st.warning("All fields are required. Please check the fields for errors.")

# Step 2: Connect to gpt and execute "Cv Analysis" Task
if current_step == 2:
    # Temp folder
    temp_path = get_temp_path()
    # Get Crew Data
    agent_data = GetAgentData()
    task_data = GetTaskData()
    # Applicant  name
    name = responses["name"]
    # Assistant message
    msg = st.chat_message("assistant",  avatar=f"{assistant_avatar_path}")
    msg.html(f"<b>HYS-Assistant</b>: {name}, <i>I am working on your resume. Please give me some time for analysis. This should not take long...</i>")
    # Loader
    with st.spinner("The assistant is running. Please stand by..."):
        with open(f"{temp_path}/resume.txt") as r:
            resume = r.read()
        with open(f"{temp_path}/vacancy.txt") as r:
            vacancy = r.read()
        # Get the cv analyst agent
        cv_analyst = agent_data.return_cv_analyst()
        # Get cv  analysis task
        cv_analyze = task_data.return_task('Cv Analyst', cv_analyst, vac=f"{vacancy}", res=f"{resume}")
        # Execute the task
        fist_analysis = cv_analyze.execute()
        with open(os.path.join(temp_path, "first_analysis.txt"), "w") as f:
            f.write("FIRST ANALYSIS:\n")
            f.write("----------------------------\n\n")
            f.write(fist_analysis)
            f.flush()
    st.session_state['current_step'] = current_step + 1
    st.rerun()
# Step 3: Connect to gpt and execute "Generate Questions" Task
if current_step == 3:
    # Temp folder
    temp_path = get_temp_path()
    # Get Crew Data
    agent_data = GetAgentData()
    task_data = GetTaskData()
    # Applicant name
    name = responses["name"]
    msg = st.chat_message("assistant", avatar=f"{assistant_avatar_path}")
    msg.html("<b>HYS-Assistant</b>: <i>Please give me some more time for analysis. We are almost there</i>")
    with open(f"{temp_path}/first_analysis.txt") as fr:
        first_analysis = fr.read()
        fr.flush()
    with st.spinner("The analysis is still running. Please stand by..."):
        hr_interviewer = agent_data.return_hr_interviewer()
        hr_interview = task_data.return_task('Human Resources Manager', hr_interviewer, first_analysis=first_analysis)
        questions = hr_interview.execute()
        with open(os.path.join(temp_path, "questions.json"), "w") as fq:
            fq.write(questions)
            fq.flush()
    st.session_state['current_step'] = current_step + 1
    st.rerun()
# Step 4 - Display additional questions
if current_step == 4:
    # Temp folder
    temp_path = get_temp_path()
    # Applicant name
    name = responses["name"]
    questions_path = f"{temp_path}/questions.json"
    if is_valid_json(questions_path):
        with open(questions_path) as q:
            questions = q.read()
        result_analysis_json = json.loads(questions)
        questions = result_analysis_json.get('questions', [])
        message = st.chat_message("assistant", avatar=f"{assistant_avatar_path}")
        message.html(
            f"<b>HYS-Assistant</b>: *{name}*, **please answer these questions to better analyze your suitability for the vacancy:**")
        num_questions = len(questions)
        answers = st.session_state.get('answers', [''] * num_questions)
        question_step = st.session_state.get('question_step', 1)
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
                        st.rerun()
                    else:
                        st.warning("Please answer all questions before proceeding.")
            elif question_step == 2:
                for i, question in enumerate(questions[5:]):
                    answers[i + 5] = st.text_input(f"{i + 6}. {question}", value=answers[i + 5], key=f"q_{i + 5}")
                col1, col2 = st.columns([11, 2])
                if col1.button("Previous"):
                    st.session_state['answers'] = answers
                    st.session_state['question_step'] = 1
                    st.rerun()
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
                        st.rerun()
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
                    st.rerun()
                else:
                    st.warning("Please answer all questions before proceeding.")

    else:
        # If there is an error with questions and/or if there are no questions, continue to final report
        with open(os.path.join(f"{temp_path}", "questions_answers.txt"), "w") as f:
            f.write(f"There were no additional questions to ask to the candidate or there was an error with questions file.")
        st.session_state['current_step'] = current_step + 1
        st.rerun()
# Step 5 - Send all analysis for final  report
if current_step == 5:
    # Temp folder
    temp_path = get_temp_path()
    # Get Crew Data
    agent_data = GetAgentData()
    task_data = GetTaskData()
    # Applicant name
    name = responses["name"]
    # All files that should have been created
    files_to_read = [
        f"{temp_path}/vacancy.txt",
        f"{temp_path}/resume.txt",
        f"{temp_path}/first_analysis.txt",
        f"{temp_path}/questions_answers.txt"
    ]
    for file_path in files_to_read:
        data = ""
        # Check if the files exist
        if os.path.exists(file_path):
            # Save in a var all file contents
            with open(file_path, 'r') as fa:
                data += fa.read()
        else:
            data += f"{file_path} was not found."
    # Send to agent for analysis

    # AOK CONTINUE HERE