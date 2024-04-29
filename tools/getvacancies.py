import pandas as pd


class GetVacData:
    def __init__(self):
        sheet_name = 'Vacancies'  # replace with your own sheet name
        sheet_id = '14r4OdQPCmkvKk1pdSeFi_IKVmtU5iGpYGypIv5itnec'  # replace with your sheet's ID

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        self.data = pd.read_csv(url).fillna('Unknown')

    def sheet_headers(self):
        # Get the first row of the DataFrame
        first_row = self.data.iloc[0]

        # Filter columns to exclude those with empty values in the first row
        non_empty_columns = first_row[first_row != 'Unknown']

        return non_empty_columns.index.tolist()


    def get_vacancy_names(self):
        # Select the 'Vacancy Name' column
        vacancy_names = self.data['Vacancy Name']
        vacancy_names = vacancy_names.tolist()
        return vacancy_names

    def get_custom_column(self, vacancy_name, column_name):
        try:
            # Select the column for the specified vacancy name
            selected_column = self.data.loc[self.data['Vacancy Name'] == vacancy_name, column_name]

            # Check if any rows were found
            if not selected_column.empty:
                # Handle missing values
                selected_column = selected_column.fillna('Unknown')
                # Return the selected column
                return selected_column.tolist()
            else:
                return f"No data found for 'Vacancy Name' equals {vacancy_name}"
        except KeyError:
            return f"Column '{column_name}' not found"
        except Exception as e:
            return f"An error occurred: {e}"

    def get_selected_vacancy_details(self, selected_vacancy):
        headers = self.sheet_headers()
        result = []  # Initialize an empty list to store the result lines
        for header in headers:
            values = self.get_custom_column(selected_vacancy, header)
            if '\n' in values[0]:
                # Replace double newline characters with a single newline character
                values[0] = values[0].replace('\n\n', '\n')
                # Check if the value ends with a single newline character
                if values[0].endswith('\n'):
                    # Remove the last newline character
                    values[0] = values[0][:-1]
                # Format the value with line breaks and indentation
                formatted_value = "\n\t".join(values[0].split('\n'))
                result.append(f'"{header}" :\n\t{formatted_value}')
            else:
                result.append(f'"{header}" : {values[0]}')

        # Join the result lines with commas and add a line break before each line
        return '\n'.join(result)