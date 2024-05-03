from tools.db_connect import DBConnect

with DBConnect() as db:
    folder_name = db.create_temp()
    db.insert_into_files(folder_name=folder_name, file_name='example_file', file_type='txt', content='example_content')