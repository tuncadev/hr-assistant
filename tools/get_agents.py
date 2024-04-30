import os

import pandas as pd
from crewai import Agent
from langchain_openai import ChatOpenAI


class GetAgentData:
    def __init__(self):
        sheet_name = 'Agents'  # replace with your own sheet name
        sheet_id = '1vmcwKyoDp3quMJO99FuuY6Et9m_MPfsfmzeVK-nlGT4'  # replace with your sheet's ID
        # OpenAI Environment
        openai_api = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = str(openai_api)
        self.open_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.1
        )
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        self.data = pd.read_csv(url).fillna('Unknown')

    def get_sheet_headers(self):  # Get the first row of the DataFrame
        first_row = self.data.iloc[0]
        # Filter columns to exclude those with empty values in the first row
        non_empty_columns = first_row[first_row != 'Unknown']
        return non_empty_columns.index.tolist()

    def get_custom_column(self, agent_name, column_name):
        try:
            # Select the column for the specified vacancy name
            selected_column = self.data.loc[self.data['role'] == agent_name, column_name]

            # Check if any rows were found
            if not selected_column.empty:
                # Handle missing values
                selected_column = selected_column.fillna('Unknown')
                # Return the selected column
                return selected_column.tolist()
            else:
                return f"No data found for 'Vacancy Name' equals {agent_name}"
        except KeyError:
            return f"Column '{column_name}' not found"
        except Exception as e:
            return f"An error occurred: {e}"

    def return_cv_analyst(self):
        agent_name = "Cv Analyst"
        headers = self.get_sheet_headers()
        agent_details = {}
        found_agent = False
        for role in self.data["role"]:
            if role == agent_name:
                agent_details["role"] = role
                for header in headers:
                    details = self.get_custom_column(agent_name, header)
                    # Check if details is a list with a single boolean element
                    if isinstance(details, list) and len(details) == 1 and isinstance(details[0], bool):
                        agent_details[header] = details[0]
                    else:
                        agent_details[header] = details
                found_agent = True
                break  # Exit the loop once the agent is found
        if not found_agent:
            return "NO"
        return Agent(
            role=agent_details['role'][0],
            goal=agent_details['goal'][0],
            backstory=agent_details['backstory'][0],
            allow_delegation=agent_details['allow_delegation'],
            verbose=agent_details['verbose'],
            llm=self.open_llm
        )

    def return_hr_interviewer(self):
        agent_name = "Human Resources Manager"
        headers = self.get_sheet_headers()
        agent_details = {}
        found_agent = False
        for role in self.data["role"]:
            if role == agent_name:
                agent_details["role"] = role
                for header in headers:
                    details = self.get_custom_column(agent_name, header)
                    # Check if details is a list with a single boolean element
                    if isinstance(details, list) and len(details) == 1 and isinstance(details[0], bool):
                        agent_details[header] = details[0]
                    else:
                        agent_details[header] = details
                found_agent = True
                break  # Exit the loop once the agent is found
        if not found_agent:
            return "NO"
        return Agent(
            role=agent_details['role'][0],
            goal=agent_details['goal'][0],
            backstory=agent_details['backstory'][0],
            allow_delegation=agent_details['allow_delegation'],
            verbose=agent_details['verbose'],
            llm=ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.1
            )
        )

    def return_hr_general_manager(self):
        agent_name = "Human Resources General Manager"
        headers = self.get_sheet_headers()
        agent_details = {}
        found_agent = False
        for role in self.data["role"]:
            if role == agent_name:
                agent_details["role"] = role
                for header in headers:
                    details = self.get_custom_column(agent_name, header)
                    # Check if details is a list with a single boolean element
                    if isinstance(details, list) and len(details) == 1 and isinstance(details[0], bool):
                        agent_details[header] = details[0]
                    else:
                        agent_details[header] = details
                found_agent = True
                break  # Exit the loop once the agent is found
        if not found_agent:
            return "NO"
        return Agent(
            role=agent_details['role'][0],
            goal=agent_details['goal'][0],
            backstory=agent_details['backstory'][0],
            allow_delegation=agent_details['allow_delegation'],
            verbose=agent_details['verbose'],
            llm=ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.1
            )
        )
