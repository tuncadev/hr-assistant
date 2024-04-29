import os
import uuid
import streamlit as st
from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from tools.getvacancies import GetVacData
from tools.read_file import ReadFileContents

# OpenAI Environment
openai_api = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = str(openai_api)
open_llm = ChatOpenAI(
    model_name="gpt-4-turbo",
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
# App functions end #


# Agents #
##############################################
def cv_analyst():
    return Agent(
        role='Cv Analyst',
        goal='Analyze the given Resume context and rewrite it in the required format.',
        backstory="""
        You are an experienced professional Senior Human Resources Manager. 
        You have 20+ years of experience in job interviews and resume reviewing. 
        You can look into a resume and tell where the gaps are between the vacancy requirements and the resume content.',
        """,
        allow_delegation=False,
        verbose=True,
        llm=open_llm
    )


##############################################
hr_interviewer = Agent(
    role='Human Resources Manager',
    goal="""
    Read the analysis report of a resume for a certain job vacancy. 
    Create minimum 6 and maximum of 10 questions to ask to the candidate to gather more information (if needed).
    """,
    backstory="""
    You are an experienced Senior Human Resources Manager. 
    You have 25+ years of experience in job interviews and resume reviewing. 
    You can read the report of a resume and create some questions to ask to the candidate for further clarification of vacancy satisfactory analysis.
    """,
    allow_delegation=False,
    verbose=True,
    llm=open_llm
)


##############################################
hr_manager = Agent(
    role='Senior Human Resources Manager',
    goal="""
           * Read vacancy details.
           * Read the first analysis report of a resume.
           * Read the resume details. 
           * Read the additional questions and answers of the candidate from the interview.
           * Write a final report about the candidate. How suitable he is for the position. 
           * Pay attention to vacancy requirements and how well the candidate fills the requirements.
           """,
    backstory="""
           You are an extremely professional, very experienced  Senior Human Resources Manager. 
           You have 25+ years of experience in job interviews and resume reviewing. 
           You can read the report of a resume and results of an interview and write a professional report about the candidate.
           You do not improvise or imagine. You work with facts.
           """,
    allow_delegation=False,
    verbose=True,
    llm=open_llm
)


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


# Tasks #
##############################################
def cv_analysis_task(vac=None, res=None):
    if vacancy and resume:
        return Task(
            description=f"""
                * Read this information about the vacancy: {vacancy} \n\n.
                * Read this contents of a resume: {resume} \n\n.
                * Do not improvise,  do not make conclusions if there is not enough information. 
                * Just work with real facts and information.
                * The goal is to analyze the given 'RESUME', and write a 'First analysis report'.
                * Search in the resume and find the matching information for each "Vacancy Requirements" and "would be plus" item
                * Rate from 0% to 100% the information found in the resume. 
                * 0% = No information found, 
                * 100% = The information in the resume is 100% guarantees that the requirement/woule be plus was met.  
                * "Work Experience" must be detailed at least for one last place of employment. ie: Company name, start-end dates, references and etc.
                * Do not rate "Work Experience" just by words and sentences. Seek for detailed information such as: company name, start-end dates, references and etc.
                * Foreign language level must be referenced in resume to receive more  than 80%. ie: English Level: C+ ,Advanced, courses, diplomas and etc.
                * Do not rate foreign language level by the resume contains. Seek for detailed information.
                * Use the "expected output" for reference. 
               """,
            expected_output=f"""
            Requirement: Name of requirement in vacancy details (% Your analysis in percentage) \n
            \t Reason: Explain your grounds. Why you gave that rating; \n\n
            
            Would be plus: Name of Would be plus in vacancy details (% Your analysis in percentage) \n
            \t Reason: Explain your grounds. Why you gave that rating; \n\n
            """,
            agent=cv_analyst()
        )


# Set Defaults
current_step = st.session_state.get('current_step', 1)
responses = st.session_state.get('responses', {})
selected_vacancy_value = responses.get("selected_vacancy", "")
vacancy_data = GetVacData()
vacancy_headers = vacancy_data.sheet_headers()
vacancy_names = vacancy_data.get_vacancy_names()
index = None if not selected_vacancy_value or selected_vacancy_value not in vacancy_names else vacancy_names.index(
    selected_vacancy_value)
# Set the temp path
temp_path = get_temp_path()

# Step 1: Get user and vacancy information
if current_step == 1:
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
                        f.write(cv_contents)
                # Get the selected vacancy details
                if vacancy_headers:
                    vacancy_details = vacancy_data.get_selected_vacancy_details(selected_vacancy)
                    with open(os.path.join(temp_path, "vacancy.txt"), "w") as f:
                        f.write(vacancy_details)
                else:
                    vacancy_details = "Vacancy not found"
            st.session_state['current_step'] = current_step + 1
            st.rerun()
        else:
            st.warning("All fields are required. Please check the fields for errors.")

# Step 2: Connect to gpt and execute tasks
if current_step == 2:
    with open(f"{temp_path}/resume.txt") as r:
        resume = r.read()
    with open(f"{temp_path}/vacancy.txt") as r:
        vacancy = r.read()
    fist_analysis = cv_analysis_task(res=resume, vac=vacancy).execute()


