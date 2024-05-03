import os
import random
import string
import sqlite3

class DBConnect:

    def __init__(self, db_name='hrdb.sqlite', db_folder='db'):
        current_dir = os.path.dirname(
            os.path.abspath(__file__))  # Get the directory of the current
        project_dir = os.path.dirname(current_dir)  # Get the parent app directory
        db_path = os.path.join(project_dir, db_folder, db_name)
        self.db_path = db_path
        self.conn = None
        self.c = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.c = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    # Generate a random key for each applicant
    @staticmethod
    def get_random_string(length):
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for i in range(length))

    # Insert into DB new applicant details
    def create_temp(self, name, email, selected_vac_name, selected_vac_details):
        while True:
            applicant_key = self.get_random_string(10)  # Generate a 10-character random string
            self.c.execute("SELECT applicant_key FROM applicants WHERE applicant_key = ?", (applicant_key,))
            existing_folder = self.c.fetchone()
            if existing_folder is None or not existing_folder:
                break  # Exit the loop if the folder name is unique or if there are no records
        self.c.execute("INSERT INTO applicants (applicant_key, name, email, selected_vac_name, selected_vac_details) VALUES (?, ?, ?, ?, ?)",
                       (applicant_key, name, email, selected_vac_name, selected_vac_details))
        self.conn.commit()
        return applicant_key


    # Connections for Vacancies
    def is_vacancies_table_empty(self):
        self.c.execute("SELECT COUNT(*) FROM vacancies")
        result = self.c.fetchone()
        return result[0] == 0

    def update_vacancy(self, vacancy):
        vacancy_name = vacancy['Vacancy Name']
        self.c.execute("UPDATE vacancies SET Vacancy_Requirements=?, Vacancy_Requirements_Affect=?, "
                       "Vacancy_Would_Be_Plus=?, Vacancy_Would_Be_Plus_Affect=?, date_updated=CURRENT_TIMESTAMP "
                       "WHERE Vacancy_Name=?", (vacancy['Vacancy Requirements'], vacancy['Vacancy Requirements affect'],
                                                vacancy['Vacancy Would be Plus'], vacancy['Vacancy Would be Plus Affect'],
                                                vacancy_name))
        self.conn.commit()

    def delete_vacancy(self, vacancy_name):
        self.c.execute("DELETE FROM vacancies WHERE Vacancy_Name = ?", (vacancy_name,))
        self.conn.commit()

    def insert_into_vacancies(self, vacancy):
        self.c.execute("INSERT INTO vacancies (Vacancy_Name, Vacancy_Requirements, Vacancy_Requirements_Affect, "
                       "Vacancy_Would_Be_Plus, Vacancy_Would_Be_Plus_Affect, date_created, date_updated) "
                       "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                       (vacancy['Vacancy Name'], vacancy['Vacancy Requirements'], vacancy['Vacancy Requirements affect'],
                        vacancy['Vacancy Would be Plus'], vacancy['Vacancy Would be Plus Affect']))
        self.conn.commit()

    def insert_or_update_vacancies(self, vacancies):
        for vacancy in vacancies:
            vacancy_name = vacancy['Vacancy Name']
            self.c.execute("SELECT * FROM vacancies WHERE Vacancy_Name=?", (vacancy_name,))
            existing_vacancy = self.c.fetchone()
            if existing_vacancy:
                self.update_vacancy(vacancy)
            else:
                self.insert_into_vacancies(vacancy)

    def get_vacancy_names(self):
        self.c.execute("SELECT Vacancy_Name FROM vacancies")
        vacancy_names = self.c.fetchall()
        return [name[0] for name in vacancy_names]

    def get_vac_details(self, vacancy_name):
        self.c.execute("SELECT * FROM vacancies WHERE Vacancy_Name=?", (vacancy_name,))
        vacancy_details = self.c.fetchone()
        headers = self.get_vacancy_headers()
        formatted_details = {}
        if vacancy_details:
            for header, value in zip(headers[1:], vacancy_details[1:]):
                formatted_details[header] = value
        return formatted_details

    def get_vacancy_headers(self):
        self.c.execute("PRAGMA table_info(vacancies)")
        headers = self.c.fetchall()
        column_names = [header[1] for header in headers]
        return column_names

    def insert_into_resumes(self, applicant_key=None, content=None):
        self.c.execute("INSERT INTO resumes (applicant_key, content) VALUES (?, ?)", (applicant_key, content))
        self.conn.commit()

    def select_from_resumes(self, applicant_key=None):
        query = f"SELECT content FROM resumes WHERE applicant_key = '{applicant_key}'"
        self.c.execute(query)
        # Fetch the results if needed
        result = self.c.fetchone()
        self.conn.commit()
        return "\n".join(result)  # Return the fetched result

    def get_selected_vac_details(self, applicant_key=None):
        self.c.execute("SELECT selected_vac_details FROM applicants WHERE applicant_key=?", (applicant_key,))
        vacancy_details = self.c.fetchone()
        self.conn.commit()
        return vacancy_details

    def insert_into_reports(self, applicant_key=None, report_table=None, content=None):
        query = f"INSERT INTO {report_table} (applicant_key, content) VALUES (?, ?)"
        self.c.execute(query, (applicant_key, content))
        self.conn.commit()

    def get_applicant_name(self, applicant_key=None):
        self.c.execute("SELECT name FROM applicants WHERE applicant_key=?", (applicant_key,))
        applicant_name = self.c.fetchone()
        self.conn.commit()
        return applicant_name

    def custom_query(self,folder_name=None, query=None):
        self.c.execute("SELECT id FROM folders WHERE folder_name = ?", (folder_name,))
        folder_id = self.c.fetchone()[0]
        if query:
            self.c.execute(query)
            result = self.c.fetchone()
            return result
        else:
            return "No results found"

