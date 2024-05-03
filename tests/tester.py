import random
import string
import sqlite3

class DBConnect:

    def __init__(self, db_path='../db/hrdb.sqlite'):
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

    @staticmethod
    def get_random_string(length):
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for i in range(length))

    def create_temp(self):
        while True:
            temp_name = self.get_random_string(10)  # Generate a 10-character random string
            self.c.execute("SELECT folder_name FROM folders WHERE folder_name = ?", (temp_name,))
            existing_folder = self.c.fetchone()
            if existing_folder is None or not existing_folder:
                break  # Exit the loop if the folder name is unique or if there are no records
        self.c.execute("INSERT INTO folders (folder_name) VALUES (?)", (temp_name,))
        self.conn.commit()
        return temp_name

    def insert_into_files(self, folder_name=None, file_name=None, file_type=None, content=None):
        self.c.execute("SELECT id FROM folders WHERE folder_name = ?", (folder_name,))
        folder_id = self.c.fetchone()[0]
        self.c.execute("INSERT INTO files (folder_id, file_name, file_type, content) VALUES (?, ?, ?, ?)", (folder_id, file_name, file_type, content))
        self.conn.commit()


with DBConnect() as db:
    folder_name = db.create_temp()
    db.insert_into_files(folder_name=folder_name, file_name='example_file', file_type='txt', content='example_content')