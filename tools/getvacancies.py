import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GetVacanciesData():

    def __init__(self):
        # Define the scope and credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)

        # Authorize the client
        client = gspread.authorize(credentials)

        # Open the Google Sheet by its URL
        sheet_url = 'https://docs.google.com/spreadsheets/d/14r4OdQPCmkvKk1pdSeFi_IKVmtU5iGpYGypIv5itnec/edit#gid=0'
        self.sheet = client.open_by_url(sheet_url)


    def get_vacancy_names(self):
        # Get the first sheet in the workbook
        worksheet = self.sheet.sheet1

        # Get all values in the sheet
        vacancies = worksheet.get_all_values()

        # Loop through each row (excluding the header) and retrieve the information
        vacancy_names = [vacancy[0] for vacancy in vacancies[1:]]  # Assuming vacancy name is in the first column (index 0)
        return vacancy_names

    def get_vacancy_info(self, vacancy_name):
        # Get the first sheet in the workbook
        worksheet = self.sheet.sheet1

        # Get all values in the sheet
        vacancies = worksheet.get_all_values()

        # Find the row corresponding to the selected vacancy
        for vacancy in vacancies[1:]:
            if vacancy[0] == vacancy_name:  # Vacancy name is in the first column (index 0)
                vacancy_info = {
                    'name': vacancy[0],
                    'requirements': vacancy[1],
                    'requirements_affect': vacancy[2],
                    'would_be_plus': vacancy[3],
                    'would_be_plus_affect': vacancy[4]
                }

                return vacancy_info

        return None  # Return None if vacancy not found