import yaml
import os
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from langchain_openai import ChatOpenAI


class CVAnalystCrew:
    agents_config_path = os.path.join(os.path.dirname(__file__), "config/agents.yaml")
    tasks_config_path = os.path.join(os.path.dirname(__file__), "config/tasks.yaml")

    def __init__(self) -> None:
        with open(self.agents_config_path, 'r') as file:
            self.agents_config = yaml.safe_load(file)
        with open(self.tasks_config_path, 'r') as file:
            self.tasks_config = yaml.safe_load(file)

        self.ai_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0
        )

    def cv_analyst(self) -> Agent:

        return Agent(
            role='Cv Analyst',
            goal='Analyze the given Resume context and rewrite it in the required format.',
            backstory='You are an experienced Senior Human Resources Manager. You have 20+ years of experience in job interviews and resume reviewing. You can look into a resume and tell where the gaps are between the vacancy requirements and the resume content.',
            allow_delegation=False,
            verbose=True,
            llm=self.ai_llm
        )

    def hr_interviewer(self) -> Agent:
        return Agent(
            role='Human Resources Manager',
            goal='Read the analysis report of a resume for a certain job vacancy. Create minimum 6 and maximum of 10 questions to ask to the candidate to gather more information (if needed).',
            backstory='You are an experienced Senior Human Resources Manager. You have 25+ years of experience in job interviews and resume reviewing. You can read the report of a resume and create some questions to ask to the candidate.',
            allow_delegation=False,
            verbose=True,
            llm=self.ai_llm
        )

    def hr_manager(self) -> Agent:
        return Agent(
            role='Senior Human Resources Manager',
            goal="""
            Read vacancy details, read the first analysis report of a resume, read the resume details, read the additional questions and answers of the candidate from the interview. 
            Write a final report about the candidate. How suitable he is for the position. 
            Pay attention to vacancy requirements and how well the candidate fills the requirements.
            """,
            backstory="""
            You are an experienced Senior Human Resources Manager. 
            You have 25+ years of experience in job interviews and resume reviewing. 
            You can read the report of a resume and results of an interview and write a professional report about the candidate.
            """,
            allow_delegation=False,
            verbose=True,
            llm=self.ai_llm
        )


    def cv_analysis_task(self, fq=None) -> Task:
        vacancy = fq["vacancy"]
        resume = fq["resume"]
        expected_output = fq["expected_output"]

        return Task(
            description=f"""
               * Read this information about the vacancy: {vacancy} \n\n.
                * Read this contents of a resume: {resume} \n\n.
                * Do not improvise,  do not make conclusions if there is not enough information. Just work with real facts and information.
                * The goal is to analyze the given 'RESUME', and write a 'First analysis report' the information you gathered from the "Resume" in the given format in the "expected_output". 
                ** Where you see "Agent analysis' put your thoughts in percentages, how much does the information in the "Resume" match requirements.
                ** And where you see "why", explain your chain of thoughts, the reason you gave more than 0%. 
                ** If you can't find ebough information in resume put "No information found" in "why".
                ** Each paragraph should be in a new line-break.
            """,
            expected_output=f"{expected_output}",
            agent=self.cv_analyst()
        )

    def hr_manager_task(self, first_analysis_report) -> Task:
        return Task(
            description=f"""
                Read the report "first analysis report". \n
                "First analysis report": {first_analysis_report} \n\n
                Analyze the report and where you see less than 100%, generate questions to ask to the candidate in order to gather more information.
                Only ask questions for areas less than 100%.
                Output must be in JSON format.
                The questions must be sharp, well-understood, brief and mostly only Yes/No questions.
            """,
            expected_output="""
             A nicely formatted analysis in JSON Format with up to 10 questions to ask to the candidate, to understand weather he/she meets the requirements or not. \n 
            The key for JSON format MUST ALWAYS BE "question" (case sensitive!) and the values are the questions. \n
            Example:
              "questions" :
                "Question 1"
                "Question 2"
                "Question 3"
                "Question 4"
                "Question 5"
            """,
            agent=self.hr_interviewer()
        )

    def hr_manager_report_task(self, q=None) -> Task:
        first_analysis_report = q["first_analysis_report"]
        vacancy_details = q["vacancy_details"]
        resume = q["resume"]
        questions_answers = q['questions_answers']
        return Task(
            description=f"""
            Step 1) First read the "Vacancy details", then read the "Resume". \n
            Step 2) After Step 1, read the "First analysis report". \n
            Step 3) After Step 2, read the "questions" and the "answers" the candidate gave during first interview. \n 
            Step 4) After Step 3, write a detailed report about the candidate.  Mention candidate's suitability to the vacancy. \n
            Explain professionally how you came up with your analysis. \n\n
            "Vacancy details: " \n {vacancy_details} \n\n
            "Resume :" \n {resume} \n\n
            "First analysis report" : \n\n {first_analysis_report}
            "Questions and answers" : \n\n {questions_answers}
            Analyze the previous reports, read the "answers" the applicant provided and analyze applicant's suitability for the vacancy.
            """,
            expected_output="A detailed professional report about the candidate. "
                            "How well he suits the vacancy."
                            "What percentage you think he gets considering the suitability of the vacancy, "
                            "vacancy requirements and candidate's resume and answers to additinonal questions",
            agent=self.hr_manager()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.cv_analyst(), self.hr_interviewer(), self.hr_manager()],
            tasks=[self.cv_analysis_task(), self.hr_manager_task(), self.hr_manager_report_task()],
            process=Process.sequential,
            verbose=2
        )