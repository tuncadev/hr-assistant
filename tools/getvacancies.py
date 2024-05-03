import pandas as pd
from tools.db_connect import DBConnect


class GetVacData:
    def __init__(self):
        sheet_name = 'Vacancies'  # replace with your own sheet name
        sheet_id = '14r4OdQPCmkvKk1pdSeFi_IKVmtU5iGpYGypIv5itnec'  # replace with your sheet's ID

        self.url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        self.data = pd.read_csv(self.url).fillna('Unknown')

    def init_vacancies(self):
        try:
            with DBConnect() as db:
                vacancies = self.data.to_dict('records')
                existing_vacancies = db.get_vacancy_names()

                # Check for vacancies to remove
                for existing_vacancy in existing_vacancies:
                    if existing_vacancy not in [v['Vacancy Name'] for v in vacancies]:
                        db.delete_vacancy(existing_vacancy)

                # Update or insert vacancies
                if db.is_vacancies_table_empty():
                    for vacancy in vacancies:
                        db.insert_into_vacancies(vacancy)
                else:
                    for vacancy in vacancies:
                        if vacancy['Vacancy Name'] in existing_vacancies:
                            db.update_vacancy(vacancy)
                        else:
                            db.insert_into_vacancies(vacancy)

            return True
        except Exception as e:
            error = f"There was an error with DB Connection. Please contact developers and give this error: {e}"
            return error

